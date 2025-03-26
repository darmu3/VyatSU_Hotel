import requests
from PySide6.QtWidgets import (
    QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QMessageBox, QCheckBox, QFormLayout, QComboBox, QSizePolicy
)

class AdminWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.tabs.addTab(self.create_add_user_tab(), "Добавить пользователя")
        self.tabs.addTab(self.create_update_user_tab(), "Обновить пользователя")

        self.setLayout(main_layout)
        self.setMinimumSize(500, 400)

    def create_add_user_tab(self):
        tab = QWidget()
        form = QFormLayout()

        self.add_surname = QLineEdit()
        self.add_name = QLineEdit()
        self.add_patronymic = QLineEdit()
        self.add_login = QLineEdit()
        self.add_password = QLineEdit()
        self.add_password.setEchoMode(QLineEdit.Password)
        self.add_positionid = QComboBox()

        form.addRow("Фамилия:", self.add_surname)
        form.addRow("Имя:", self.add_name)
        form.addRow("Отчество:", self.add_patronymic)
        form.addRow("Логин:", self.add_login)
        form.addRow("Пароль:", self.add_password)
        form.addRow("Роль:", self.add_positionid)

        add_btn = QPushButton("Добавить пользователя")
        add_btn.clicked.connect(self.add_user_handler)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(add_btn)
        btn_layout.addStretch()
        form.addRow(btn_layout)

        tab.setLayout(form)
        return tab

    def create_update_user_tab(self):
        tab = QWidget()
        form = QFormLayout()

        self.user_combo = QComboBox()
        self.user_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        load_btn = QPushButton("Загрузить данные")
        load_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        load_btn.clicked.connect(self.load_user_data)
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.user_combo)
        h_layout.addWidget(load_btn)
        form.addRow("Пользователь:", h_layout)

        self.upd_surname = QLineEdit()
        self.upd_name = QLineEdit()
        self.upd_patronymic = QLineEdit()
        self.upd_login = QLineEdit()
        self.upd_password = QLineEdit()
        self.upd_password.setEchoMode(QLineEdit.Password)
        self.upd_positionid = QComboBox()
        self.upd_is_blocked = QCheckBox("Заблокирован")
        self.upd_failed_attempts = QLineEdit()

        for widget in (self.upd_surname, self.upd_name, self.upd_patronymic,
                       self.upd_login, self.upd_password, self.upd_positionid,
                       self.upd_failed_attempts):
            widget.setDisabled(True)
        self.upd_is_blocked.setDisabled(True)

        form.addRow("Фамилия:", self.upd_surname)
        form.addRow("Имя:", self.upd_name)
        form.addRow("Отчество:", self.upd_patronymic)
        form.addRow("Логин:", self.upd_login)
        form.addRow("Пароль:", self.upd_password)
        form.addRow("Роль:", self.upd_positionid)  # Меняем на "Роль"
        form.addRow("Блокировка:", self.upd_is_blocked)
        form.addRow("Неудачных попыток:", self.upd_failed_attempts)

        self.update_btn = QPushButton("Обновить данные пользователя")
        self.update_btn.setDisabled(True)
        self.update_btn.clicked.connect(self.update_user_handler)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.update_btn)
        btn_layout.addStretch()
        form.addRow(btn_layout)

        tab.setLayout(form)
        self.load_users()
        self.load_positions()
        return tab

    def load_positions(self):
        url = "http://127.0.0.1:8000/admin/positions"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                positions = response.json()
                self.add_positionid.clear()
                self.upd_positionid.clear()
                for pos in positions:
                    self.add_positionid.addItem(pos["name"], pos["positionid"])
                    self.upd_positionid.addItem(pos["name"], pos["positionid"])
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить список ролей")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения к серверу: {e}")

    def load_users(self):
        url = "http://127.0.0.1:8000/admin/users"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                users = response.json()
                self.user_combo.clear()
                for user in users:
                    display_text = f"{user['surname']} {user['name']} {user['patronymic']} ({user['login']})"
                    self.user_combo.addItem(display_text, user['userid'])
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить список пользователей")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения к серверу: {e}")

    def load_user_data(self):
        userid = self.user_combo.currentData()
        if not userid:
            QMessageBox.warning(self, "Ошибка", "Пользователь не выбран")
            return

        url = f"http://127.0.0.1:8000/admin/user/{userid}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                self.upd_surname.setText(data.get("surname", ""))
                self.upd_name.setText(data.get("name", ""))
                self.upd_patronymic.setText(data.get("patronymic", ""))
                self.upd_login.setText(data.get("login", ""))
                self.upd_password.setText(data.get("password", ""))
                self.upd_failed_attempts.setText(str(data.get("failed_attempts", 0)))
                self.upd_is_blocked.setChecked(data.get("is_blocked", False))

                # Выбираем соответствующую роль в выпадающем списке
                positionid = data.get("positionid", None)
                if positionid:
                    index = self.upd_positionid.findData(positionid)
                    if index != -1:
                        self.upd_positionid.setCurrentIndex(index)

                for widget in (self.upd_surname, self.upd_name, self.upd_patronymic,
                               self.upd_login, self.upd_password, self.upd_positionid,
                               self.upd_failed_attempts, self.update_btn):
                    widget.setDisabled(False)
                self.upd_is_blocked.setDisabled(False)
            else:
                error_detail = response.json().get("detail", "Ошибка при загрузке данных пользователя")
                QMessageBox.warning(self, "Ошибка", error_detail)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения к серверу: {e}")

    def reset_update_fields(self):
        self.upd_surname.clear()
        self.upd_name.clear()
        self.upd_patronymic.clear()
        self.upd_login.clear()
        self.upd_password.clear()
        self.upd_positionid.clear()
        self.upd_failed_attempts.clear()
        self.upd_is_blocked.setChecked(False)
        for widget in (self.upd_surname, self.upd_name, self.upd_patronymic,
                       self.upd_login, self.upd_password, self.upd_positionid,
                       self.upd_failed_attempts, self.update_btn):
            widget.setDisabled(True)
        self.upd_is_blocked.setDisabled(True)

    def add_user_handler(self):
        positionid = self.add_positionid.currentData()  # Берем ID из выпадающего списка

        data = {
            "surname": self.add_surname.text().strip(),
            "name": self.add_name.text().strip(),
            "patronymic": self.add_patronymic.text().strip(),
            "login": self.add_login.text().strip(),
            "password": self.add_password.text().strip(),
            "positionid": positionid
        }
        url = "http://127.0.0.1:8000/admin/add_user"
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                QMessageBox.information(self, "Успех", "Пользователь успешно добавлен!")
                self.load_users()
            else:
                error_detail = response.json().get("detail", "Ошибка при добавлении пользователя")
                QMessageBox.warning(self, "Ошибка", error_detail)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения к серверу: {e}")

    def update_user_handler(self):
        userid = self.user_combo.currentData()
        positionid = self.upd_positionid.currentData()
        if not userid:
            QMessageBox.warning(self, "Ошибка", "Пользователь не выбран")
            return

        try:
            failed_attempts = int(self.upd_failed_attempts.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Количество неудачных попыток должно быть числом")
            return

        try:
            positionid = int(self.upd_positionid.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "PositionID должен быть числом")
            return

        data = {
            "userid": userid,
            "surname": self.upd_surname.text().strip(),
            "name": self.upd_name.text().strip(),
            "patronymic": self.upd_patronymic.text().strip(),
            "login": self.upd_login.text().strip(),
            "password": self.upd_password.text().strip(),
            "positionid": positionid,
            "is_blocked": self.upd_is_blocked.isChecked(),
            "failed_attempts": failed_attempts
        }
        url = "http://127.0.0.1:8000/admin/update_user"
        try:
            response = requests.put(url, json=data)
            if response.status_code == 200:
                QMessageBox.information(self, "Успех", "Пользователь успешно обновлен!")
                self.load_users()
                self.reset_update_fields()
            else:
                error_detail = response.json().get("detail", "Ошибка при обновлении данных")
                QMessageBox.warning(self, "Ошибка", error_detail)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения к серверу: {e}")
