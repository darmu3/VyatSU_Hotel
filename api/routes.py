from fastapi import APIRouter, HTTPException
from datetime import datetime
from models import *
from db import get_db_connection

router = APIRouter()

DEFAULT_ADMIN_PASSWORD = "12345678"

@router.post("/login")
def login(user: UserLogin):
    """
    Эндпоинт для авторизации:
      1. По логину ищем пользователя.
      2. Если is_blocked == true, возвращаем ошибку "Вы заблокированы".
      3. Если пользователь не заходил более 30 дней (last_login), блокируем его.
      4. Если пароль неверный, увеличиваем failed_attempts. При 3 неудачных попытках блокируем.
      5. Если пароль верный, сбрасываем failed_attempts и обновляем last_login.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
            SELECT userid, password, positionid, is_blocked, last_login, failed_attempts
            FROM users
            WHERE login = %s
        """, (user.username,))
    row = cursor.fetchone()

    if not row:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=401, detail="Неверные данные (логин не найден)")

    user_id, db_password, position_id, is_blocked, last_login, failed_attempts = row

    if is_blocked:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=403, detail="Вы заблокированы. Обратитесь к администратору")

    if last_login is not None:
        if (datetime.now() - last_login).days > 30:
            cursor.execute("""
                UPDATE users
                SET is_blocked = true
                WHERE userid = %s
            """, (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            raise HTTPException(status_code=403, detail="Вы заблокированы (не входили более 30 дней). Обратитесь к администратору")

    if user.password != db_password:
        failed_attempts += 1
        if failed_attempts >= 3:
            cursor.execute("""
                UPDATE users
                SET failed_attempts = %s,
                    is_blocked = true
                WHERE userid = %s
            """, (failed_attempts, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            raise HTTPException(status_code=403, detail="Вы заблокированы (3 неверных попытки). Обратитесь к администратору")
        else:
            cursor.execute("""
                UPDATE users
                SET failed_attempts = %s
                WHERE userid = %s
            """, (failed_attempts, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            remaining_attempts = 3 - failed_attempts
            raise HTTPException(status_code=401, detail=f"Вы ввели неверный логин или пароль. Пожалуйста проверьте ещё раз введенные данные. Осталось {remaining_attempts} попыток.")

    cursor.execute("""
        UPDATE users
        SET failed_attempts = 0,
            last_login = %s
        WHERE userid = %s
    """, (datetime.now(), user_id))
    conn.commit()

    cursor.close()
    conn.close()

    first_login = (db_password == DEFAULT_ADMIN_PASSWORD)

    return {
        "message": "Вы успешно авторизовались",
        "user_id": user_id,
        "position_id": position_id,
        "first_login": first_login
    }


@router.get("/admin/positions")
def get_positions():
    """
    Возвращает список позиций пользователей.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT positionid, name FROM position")
    rows = cursor.fetchall()

    positions = [{"positionid": row[0], "name": row[1]} for row in rows]

    cursor.close()
    conn.close()

    return positions


@router.post("/change_password")
def change_password(data: ChangePassword):
    """
    Эндпоинт для смены пароля.
      1. Проверяем, что old_password соответствует текущему паролю.
      2. Проверяем совпадение new_password с confirm_password.
      3. Если проверки прошли, обновляем пароль.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT password
        FROM users
        WHERE userid = %s
    """, (data.user_id,))
    result = cursor.fetchone()

    if not result:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    current_password = result[0]

    if current_password != data.old_password:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=401, detail="Текущий пароль введён неверно")

    if data.new_password != data.confirm_password:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Новый пароль не совпадает с подтверждением")

    cursor.execute("""
        UPDATE users
        SET password = %s
        WHERE userid = %s
    """, (data.new_password, data.user_id))
    conn.commit()

    cursor.close()
    conn.close()

    return {"message": "Пароль успешно изменён"}

@router.post("/admin/add_user")
def add_user(user: AddUser):
    """
    Эндпоинт для добавления нового пользователя.
    Если пользователь с указанным логином уже существует, возвращается ошибка.
    При успешном добавлении создается пользователь с is_blocked = false и failed_attempts = 0.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT userid FROM users WHERE login = %s", (user.login,))
    if cursor.fetchone() is not None:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")

    cursor.execute("""
        INSERT INTO users (surname, name, patronymic, login, password, positionid, is_blocked, failed_attempts)
        VALUES (%s, %s, %s, %s, %s, %s, false, 0)
        RETURNING userid
    """, (user.surname, user.name, user.patronymic, user.login, user.password, user.positionid))
    new_user_id = cursor.fetchone()[0]
    conn.commit()

    cursor.close()
    conn.close()
    return {"message": "Пользователь успешно добавлен", "user_id": new_user_id}

@router.put("/admin/update_user")
def update_user(user: UpdateUser):
    """
    Эндпоинт для обновления данных пользователя.
    Можно обновить фамилию, имя, отчество, логин, пароль, позицию, а также сбросить/изменить блокировку и счетчик неудачных попыток.
    Если при обновлении новый логин занят другим пользователем, возвращается ошибка.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT userid FROM users WHERE userid = %s", (user.userid,))
    if cursor.fetchone() is None:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    cursor.execute("SELECT userid FROM users WHERE login = %s AND userid != %s", (user.login, user.userid))
    if cursor.fetchone() is not None:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")

    cursor.execute("""
        UPDATE users
        SET surname = %s,
            name = %s,
            patronymic = %s,
            login = %s,
            password = %s,
            positionid = %s,
            is_blocked = %s,
            failed_attempts = %s
        WHERE userid = %s
    """, (
        user.surname,
        user.name,
        user.patronymic,
        user.login,
        user.password,
        user.positionid,
        user.is_blocked,
        user.failed_attempts,
        user.userid
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Пользователь успешно обновлен"}

@router.get("/admin/users")
def get_users():
    """
    Возвращает список пользователей с основными данными.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT userid, surname, name, patronymic, login FROM users")
    rows = cursor.fetchall()
    users = []
    for row in rows:
        users.append({
            "userid": row[0],
            "surname": row[1],
            "name": row[2],
            "patronymic": row[3],
            "login": row[4]
        })
    cursor.close()
    conn.close()
    return users

@router.get("/admin/user/{userid}")
def get_user(userid: int):
    """
    Возвращает полные данные пользователя по его идентификатору.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT userid, surname, name, patronymic, login, password, positionid, is_blocked, failed_attempts
        FROM users
        WHERE userid = %s
    """, (userid,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {
        "userid": row[0],
        "surname": row[1],
        "name": row[2],
        "patronymic": row[3],
        "login": row[4],
        "password": row[5],
        "positionid": row[6],
        "is_blocked": row[7],
        "failed_attempts": row[8]
    }

@router.put("/admin/update_user")
def update_user(user: UpdateUser):
    """
    Эндпоинт для обновления данных пользователя.
    Обновляются ФИО, логин, пароль, позиция, а также is_blocked и failed_attempts.
    Если новый логин занят другим пользователем, возвращается ошибка.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT userid FROM users WHERE userid = %s", (user.userid,))
    if cursor.fetchone() is None:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    cursor.execute("SELECT userid FROM users WHERE login = %s AND userid != %s", (user.login, user.userid))
    if cursor.fetchone() is not None:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")

    cursor.execute("""
        UPDATE users
        SET surname = %s,
            name = %s,
            patronymic = %s,
            login = %s,
            password = %s,
            positionid = %s,
            is_blocked = %s,
            failed_attempts = %s
        WHERE userid = %s
    """, (
        user.surname,
        user.name,
        user.patronymic,
        user.login,
        user.password,
        user.positionid,
        user.is_blocked,
        user.failed_attempts,
        user.userid
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Пользователь успешно обновлен"}