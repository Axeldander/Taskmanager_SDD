
from PySide6.QtWidgets import QLineEdit

from app.gui.create_user_dialog import CreateUserDialog


def test_dialog_has_required_fields(qtbot):
    dialog = CreateUserDialog()
    qtbot.addWidget(dialog)

    assert dialog.windowTitle() == "Create User"
    assert dialog.username_input is not None
    assert dialog.password_input is not None
    assert dialog.confirm_password_input is not None
    assert dialog.create_button.text() == "Create User"


def test_password_fields_are_hidden(qtbot):
    dialog = CreateUserDialog()
    qtbot.addWidget(dialog)

    assert (
        dialog.password_input.echoMode()
        == QLineEdit.EchoMode.Password
    )
    assert (
        dialog.confirm_password_input.echoMode()
        == QLineEdit.EchoMode.Password
    )


def test_dialog_rejects_empty_username(qtbot):
    dialog = CreateUserDialog()
    qtbot.addWidget(dialog)

    dialog.password_input.setText("Password12345!")
    dialog.confirm_password_input.setText("Password12345!")

    dialog.create_button.click()

    assert dialog.error_label.text() == "Username cannot be empty."


def test_dialog_rejects_short_password(qtbot):
    dialog = CreateUserDialog()
    qtbot.addWidget(dialog)

    dialog.username_input.setText("alice")
    dialog.password_input.setText("short")
    dialog.confirm_password_input.setText("short")

    dialog.create_button.click()

    assert "at least 12 characters" in dialog.error_label.text()


def test_dialog_rejects_password_mismatch(qtbot):
    dialog = CreateUserDialog()
    qtbot.addWidget(dialog)

    dialog.username_input.setText("alice")
    dialog.password_input.setText("Password12345!")
    dialog.confirm_password_input.setText("DifferentPassword123!")

    dialog.create_button.click()

    assert dialog.error_label.text() == "Passwords do not match."


def test_dialog_emits_valid_credentials(qtbot):
    dialog = CreateUserDialog()
    qtbot.addWidget(dialog)

    dialog.username_input.setText("alice")
    dialog.password_input.setText("Password12345!")
    dialog.confirm_password_input.setText("Password12345!")

    with qtbot.waitSignal(
        dialog.create_user_requested, timeout=1000
    ) as blocker:
        dialog.create_button.click()

    assert blocker.args == ["alice", "Password12345!"]
