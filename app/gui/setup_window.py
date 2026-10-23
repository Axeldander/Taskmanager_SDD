
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)


class SetupWindow(QWidget):
    setup_requested = Signal(str, str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Task Manager - Initial Setup")
        self.setMinimumSize(400, 320)

        layout = QVBoxLayout(self)

        title = QLabel("Create Administrator Account")
        title.setStyleSheet(
            "font-size: 20px; font-weight: bold;"
        )
        layout.addWidget(title)

        description = QLabel(
            "Set up the first administrator account "
            "to start using Task Manager."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(
            "Administrator username"
        )
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

        self.create_button = QPushButton(
            "Create Administrator"
        )
        self.create_button.clicked.connect(
            self._handle_setup
        )
        layout.addWidget(self.create_button)

    def _handle_setup(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirmation = self.confirm_password_input.text()

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

        if password != confirmation:
            self.error_label.setText(
                "Passwords do not match."
            )
            return

        self.error_label.clear()
        self.setup_requested.emit(username, password)

    def show_error(self, message: str):
        self.error_label.setText(message)
