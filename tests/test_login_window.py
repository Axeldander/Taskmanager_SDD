
from app.gui.login_window import LoginWindow


def test_login_window_has_required_fields(qtbot):
    window = LoginWindow()
    qtbot.addWidget(window)

    assert window.windowTitle() == "Task Manager - Login"
    assert window.username_input.placeholderText() == "Username"
    assert window.password_input.placeholderText() == "Password"
    assert window.login_button.text() == "Log In"


def test_password_field_is_hidden(qtbot):
    window = LoginWindow()
    qtbot.addWidget(window)

    assert (
        window.password_input.echoMode()
        == window.password_input.EchoMode.Password
    )


def test_login_button_emits_credentials(qtbot):
    window = LoginWindow()
    qtbot.addWidget(window)

    window.username_input.setText("alice")
    window.password_input.setText("AlicePassword123!")

    with qtbot.waitSignal(
        window.login_requested, timeout=1000
    ) as blocker:
        window.login_button.click()

    assert blocker.args == [
        "alice",
        "AlicePassword123!",
    ]
