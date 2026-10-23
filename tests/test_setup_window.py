
from PySide6.QtWidgets import QLineEdit

from app.gui.setup_window import SetupWindow


def test_setup_window_has_required_fields(qtbot):
    window = SetupWindow()
    qtbot.addWidget(window)

    assert (
        window.windowTitle()
        == "Task Manager - Initial Setup"
    )
    assert window.username_input is not None
    assert window.password_input is not None
    assert window.confirm_password_input is not None
    assert window.create_button.text() == "Create Administrator"


def test_setup_password_fields_are_hidden(qtbot):
    window = SetupWindow()
    qtbot.addWidget(window)

    assert (
        window.password_input.echoMode()
        == QLineEdit.EchoMode.Password
    )
    assert (
        window.confirm_password_input.echoMode()
        == QLineEdit.EchoMode.Password
    )


def test_setup_rejects_password_mismatch(qtbot):
    window = SetupWindow()
    qtbot.addWidget(window)

    window.username_input.setText("admin")
    window.password_input.setText("AdminPassword123!")
    window.confirm_password_input.setText(
        "DifferentPassword123!"
    )

    window.create_button.click()

    assert window.error_label.text() == "Passwords do not match."


def test_setup_rejects_short_password(qtbot):
    window = SetupWindow()
    qtbot.addWidget(window)

    window.username_input.setText("admin")
    window.password_input.setText("short")
    window.confirm_password_input.setText("short")

    window.create_button.click()

    assert "at least 12 characters" in window.error_label.text()


def test_setup_emits_valid_credentials(qtbot):
    window = SetupWindow()
    qtbot.addWidget(window)

    window.username_input.setText("admin")
    window.password_input.setText("AdminPassword123!")
    window.confirm_password_input.setText(
        "AdminPassword123!"
    )

    with qtbot.waitSignal(
        window.setup_requested, timeout=1000
    ) as blocker:
        window.create_button.click()

    assert blocker.args == [
        "admin",
        "AdminPassword123!",
    ]

