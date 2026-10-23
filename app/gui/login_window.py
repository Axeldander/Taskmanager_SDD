
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)


class LoginWindow(QWidget):
    login_requested = Signal(str, str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Task Manager - Login")
        self.setMinimumSize(380, 280)

        layout = QVBoxLayout()

        title = QLabel("Task Manager")
        title.setStyleSheet(
            "font-size: 24px; font-weight: bold;"
        )
        layout.addWidget(title)

        subtitle = QLabel("Sign in to your account")
        layout.addWidget(subtitle)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Log In")
        self.login_button.clicked.connect(
            self._handle_login
        )
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def _handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        self.login_requested.emit(username, password)

