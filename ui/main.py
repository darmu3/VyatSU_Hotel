import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from widgets.login_widget import LoginWidget
from widgets.change_widget import ChangePasswordWidget
from widgets.admin_widget import AdminWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VyatSU_Hotel")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_widget = LoginWidget()
        self.login_widget.login_success.connect(self.on_login_success)
        self.login_widget.first_login_required.connect(self.on_first_login_required)
        self.stack.addWidget(self.login_widget)

        self.change_widget = None
        self.admin_widget = None

        self.show()

    def on_first_login_required(self, user_id):
        print(f"on_first_login_required: user_id = {user_id}")
        self.change_widget = ChangePasswordWidget(user_id)
        self.change_widget.password_changed.connect(self.on_password_changed)
        self.stack.addWidget(self.change_widget)
        self.stack.setCurrentWidget(self.change_widget)
        print("Переключились на форму смены пароля.")

    def on_login_success(self, user_id, position_id):
        print(f"on_login_success: user_id = {user_id}, position_id = {position_id}")
        if position_id == 2:
            if self.admin_widget is None:
                self.admin_widget = AdminWidget()
                self.stack.addWidget(self.admin_widget)
                print("Создан виджет администратора.")
            self.stack.setCurrentWidget(self.admin_widget)
            print("Переключились на административный виджет.")
        else:
            self.login_widget.username.clear()
            self.login_widget.password.clear()
            self.stack.setCurrentWidget(self.login_widget)
            print("Остались на форме логина (не администратор).")

    def on_password_changed(self):
        print("on_password_changed вызван.")
        if self.change_widget:
            self.stack.removeWidget(self.change_widget)
            self.change_widget = None
        self.login_widget.username.clear()
        self.login_widget.password.clear()
        self.stack.setCurrentWidget(self.login_widget)
        print("Вернулись на форму логина.")

class LoginApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.main_window = MainWindow()

if __name__ == "__main__":
    app = LoginApp(sys.argv)
    sys.exit(app.exec())
