from pydantic import BaseModel

class UserLogin(BaseModel):
    username: str
    password: str

class ChangePassword(BaseModel):
    user_id: int
    old_password: str
    new_password: str
    confirm_password: str

class AddUser(BaseModel):
    surname: str
    name: str
    patronymic: str
    login: str
    password: str
    positionid: int

class UpdateUser(BaseModel):
    userid: int
    surname: str
    name: str
    patronymic: str
    login: str
    password: str
    positionid: int
    is_blocked: bool
    failed_attempts: int
