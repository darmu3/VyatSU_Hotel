import requests
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox, QSizePolicy
from PySide6.QtCore import Signal

class LoginWidget(QWidget):
    login_success = Signal(int, int)
    first_login_required = Signal(int)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setMinimumSize(300, 150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.label = QLabel("Введите логин и пароль", self)
        layout.addWidget(self.label)

        self.username = QLineEdit(self)
        self.username.setPlaceholderText("Логин")
        self.username.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.username)

        self.password = QLineEdit(self)
        self.password.setPlaceholderText("Пароль")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.password)

        self.login_button = QPushButton("Войти", self)
        self.login_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)

        layout.setStretch(0, 1)  # Заголовок
        layout.setStretch(1, 2)  # Поле логина
        layout.setStretch(2, 2)  # Поле пароля
        layout.setStretch(3, 1)  # Кнопка

        self.setLayout(layout)

    def handle_login(self):
        username = self.username.text()
        password = self.password.text()
        url = "http://127.0.0.1:8000/login"

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        try:
            response = requests.post(url, json={"username": username, "password": password})
            if response.status_code == 200:
                data = response.json()
                user_id = data.get("user_id")
                position_id = data.get("position_id")
                first_login = data.get("first_login", False)

                if first_login:
                    QMessageBox.information(self, "Авторизация", "Первый вход. Необходимо сменить пароль.")
                    self.first_login_required.emit(user_id)
                else:
                    QMessageBox.information(self, "Авторизация", data.get("message", "Вы успешно авторизовались"))
                    self.login_success.emit(user_id, position_id)
            elif response.status_code == 403:
                error_detail = response.json().get("detail", "Вы заблокированы. Обратитесь к администратору")
                QMessageBox.warning(self, "Ошибка авторизации", error_detail)
            else:
                error_detail = response.json().get("detail", "Неверные данные")
                QMessageBox.warning(self, "Ошибка авторизации", error_detail)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения к серверу: {e}")
