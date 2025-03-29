import requests
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox, QSizePolicy
from PySide6.QtCore import Signal

class ChangePasswordWidget(QWidget):
    password_changed = Signal()

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.init_ui()

    def init_ui(self):
        self.setMinimumSize(300, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.label = QLabel("Смена пароля", self)
        layout.addWidget(self.label)

        self.old_password = QLineEdit(self)
        self.old_password.setPlaceholderText("Текущий пароль")
        self.old_password.setEchoMode(QLineEdit.Password)
        self.old_password.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.old_password)

        self.new_password = QLineEdit(self)
        self.new_password.setPlaceholderText("Новый пароль")
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.new_password)

        self.confirm_password = QLineEdit(self)
        self.confirm_password.setPlaceholderText("Подтвердите новый пароль")
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.confirm_password)

        self.change_button = QPushButton("Изменить пароль", self)
        self.change_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.change_button.clicked.connect(self.handle_change_password)
        layout.addWidget(self.change_button)

        layout.setStretch(0, 1)
        layout.setStretch(1, 2)
        layout.setStretch(2, 2)
        layout.setStretch(3, 2)
        layout.setStretch(4, 1)

        self.setLayout(layout)

    def handle_change_password(self):
        old_password = self.old_password.text().strip()
        new_password = self.new_password.text().strip()
        confirm_password = self.confirm_password.text().strip()

        if not old_password or not new_password or not confirm_password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return
        if old_password != "12345678":
            QMessageBox.warning(self, "Ошибка", "Предыдущий пароль неверный")
            return
        if new_password == confirm_password:
            url = "http://127.0.0.1:8000/change_password"
            data = {
                "user_id": self.user_id,
                "old_password": old_password,
                "new_password": new_password,
                "confirm_password": confirm_password
            }

            try:
                response = requests.post(url, json=data)
                if response.status_code == 200:
                    QMessageBox.information(self, "Успех", "Пароль успешно изменён!")
                    self.password_changed.emit()
                else:
                    error_detail = response.json().get("detail", "Ошибка при смене пароля")
                    QMessageBox.warning(self, "Ошибка", error_detail)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка подключения к серверу: {e}")
        else:
            QMessageBox.warning(self, "Ошибка", "Новый пароль и пароль для подтверждения не совпадают")
            return