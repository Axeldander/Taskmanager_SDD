
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)


class CreateUserDialog(QDialog):
    create_user_requested = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Create User")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)

        title = QLabel("Create Standard User")
        title.setStyleSheet(
            "font-size: 20px; font-weight: bold;"
        )
        layout.addWidget(title)

        description = QLabel(
            "Create an account for a standard user."
        )
        layout.addWidget(description)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(
            "Password (at least 12 characters)"
        )
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        layout.addWidget(self.password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText(
            "Confirm password"
        )
        self.confirm_password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        layout.addWidget(self.confirm_password_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        layout.addWidget(self.error_label)

        self.create_button = QPushButton("Create User")
        self.create_button.clicked.connect(
            self._handle_create
        )
        layout.addWidget(self.create_button)

    def _handle_create(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not username:
            self.error_label.setText(
                "Username cannot be empty."
            )
            return

        if len(password) < 12:
            self.error_label.setText(
                "Password must contain at least 12 characters."
            )
            return

        if password != confirm_password:
            self.error_label.setText(
                "Passwords do not match."
            )
            return

        self.error_label.clear()

        if not username:
            self.show_error("Please enter a username.")
            return

        if not password:
            self.show_error("Please enter a password.")
            return

        if password != confirm_password:
            self.show_error("Passwords do not match.")
            return
        self.create_user_requested.emit(username, password)

    def show_error(self, message: str):
        self.error_label.setText(message)
