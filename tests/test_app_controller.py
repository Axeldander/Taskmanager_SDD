
from app.gui.app_controller import AppController


def test_first_launch_shows_setup_window(
    qtbot, tmp_path
):
    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'first.db').as_posix()}"
        )
    )

    controller.start()
    qtbot.addWidget(controller.current_window)

    assert (
        controller.current_window.windowTitle()
        == "Task Manager - Initial Setup"
    )

    controller.shutdown()


def test_existing_admin_shows_login_window(
    qtbot, tmp_path
):
    database_url = (
        f"sqlite:///{(tmp_path / 'existing.db').as_posix()}"
    )

    first_controller = AppController(
        database_url=database_url
    )

    first_controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )
    first_controller.shutdown()

    controller = AppController(
        database_url=database_url
    )

    controller.start()
    qtbot.addWidget(controller.current_window)

    assert (
        controller.current_window.windowTitle()
        == "Task Manager - Login"
    )

    controller.shutdown()


def test_admin_login_opens_admin_dashboard(
    qtbot, tmp_path
):
    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'admin.db').as_posix()}"
        )
    )

    controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )

    controller.start()

    login_window = controller.current_window
    qtbot.addWidget(login_window)

    login_window.username_input.setText("admin")
    login_window.password_input.setText(
        "AdminPassword123!"
    )
    login_window.login_button.click()

    assert (
        controller.current_window.windowTitle()
        == "Task Manager - Administrator"
    )

    controller.shutdown()


def test_invalid_login_stays_on_login_window(
    qtbot, tmp_path
):
    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'invalid.db').as_posix()}"
        )
    )

    controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )

    controller.start()

    login_window = controller.current_window
    qtbot.addWidget(login_window)

    login_window.username_input.setText("admin")
    login_window.password_input.setText(
        "WrongPassword123!"
    )
    login_window.login_button.click()

    assert controller.current_window is login_window
    assert not controller.auth_service.is_authenticated()
    assert login_window.error_label.text() == (
        "Incorrect username or password. Please try again."
    )

    controller.shutdown()

def test_admin_logout_returns_to_login(qtbot, tmp_path):
    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'admin_logout.db').as_posix()}"
        )
    )

    controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )
    controller.start()

    login_window = controller.current_window
    login_window.username_input.setText("admin")
    login_window.password_input.setText("AdminPassword123!")
    login_window.login_button.click()

    dashboard = controller.current_window
    assert dashboard.windowTitle() == "Task Manager - Administrator"
    assert controller.auth_service.is_authenticated()

    dashboard.logout_button.click()

    assert controller.current_window.windowTitle() == "Task Manager - Login"
    assert not controller.auth_service.is_authenticated()

    controller.shutdown()


def test_user_logout_returns_to_login(qtbot, tmp_path):
    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'user_logout.db').as_posix()}"
        )
    )

    controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )

    from app.services.user_management import UserManagementService

    controller.auth_service.login("admin", "AdminPassword123!")

    management = UserManagementService(
        controller.session_factory,
        controller.auth_service,
    )
    management.create_user("alice", "AlicePassword123!")
    controller.auth_service.logout()

    controller.start()

    login_window = controller.current_window
    login_window.username_input.setText("alice")
    login_window.password_input.setText("AlicePassword123!")
    login_window.login_button.click()

    dashboard = controller.current_window
    assert dashboard.windowTitle() == "Task Manager - My Tasks"
    assert controller.auth_service.is_authenticated()

    dashboard.logout_button.click()

    assert controller.current_window.windowTitle() == "Task Manager - Login"
    assert not controller.auth_service.is_authenticated()

    controller.shutdown()


def test_admin_dashboard_loads_database_tasks(qtbot, tmp_path):
    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'admin_tasks.db').as_posix()}"
        )
    )

    controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )

    controller.auth_service.login(
        "admin", "AdminPassword123!"
    )

    from app.services.user_management import UserManagementService

    users = UserManagementService(
        controller.session_factory,
        controller.auth_service,
    )

    alice_id = users.create_user(
        "alice", "AlicePassword123!"
    )

    controller.task_service.create_task(
        "Prepare report",
        "Finish the report",
        alice_id,
    )

    controller.auth_service.logout()
    controller.start()

    login = controller.current_window
    login.username_input.setText("admin")
    login.password_input.setText("AdminPassword123!")
    login.login_button.click()

    dashboard = controller.current_window

    assert dashboard.task_table.rowCount() == 1

    assert (
        dashboard.task_table.item(0, 1).text()
        == "Prepare report"
    )

    # The administrator sees the username, not the numeric ID.
    assert dashboard.task_table.item(0, 3).text() == "alice"

    assert dashboard.todo_count.text() == "To Do: 1"

    controller.shutdown()


def test_user_dashboard_loads_only_assigned_tasks(
    qtbot, tmp_path
):
    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'user_tasks.db').as_posix()}"
        )
    )

    controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )

    controller.auth_service.login(
        "admin", "AdminPassword123!"
    )

    from app.services.user_management import UserManagementService

    users = UserManagementService(
        controller.session_factory,
        controller.auth_service,
    )

    alice_id = users.create_user(
        "alice", "AlicePassword123!"
    )
    bob_id = users.create_user(
        "bob", "BobPassword123!"
    )

    controller.task_service.create_task(
        "Alice task", "Description", alice_id
    )
    controller.task_service.create_task(
        "Bob task", "Description", bob_id
    )

    controller.auth_service.logout()
    controller.start()

    login = controller.current_window
    login.username_input.setText("alice")
    login.password_input.setText("AlicePassword123!")
    login.login_button.click()

    dashboard = controller.current_window

    assert dashboard.task_table.rowCount() == 1
    assert (
        dashboard.task_table.item(0, 1).text()
        == "Alice task"
    )
    assert dashboard.task_table.item(0, 2).text() == "Description"


    controller.shutdown()

def test_user_status_update_is_saved_to_database(qtbot, tmp_path):
    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'status_update.db').as_posix()}"
        )
    )

    controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )
    controller.auth_service.login(
        "admin", "AdminPassword123!"
    )

    from app.services.user_management import UserManagementService
    from app.models import Task

    users = UserManagementService(
        controller.session_factory,
        controller.auth_service,
    )

    alice_id = users.create_user(
        "alice", "AlicePassword123!"
    )
    task_id = controller.task_service.create_task(
        "Prepare report", "Description", alice_id
    )

    controller.auth_service.logout()
    controller.start()

    login = controller.current_window
    login.username_input.setText("alice")
    login.password_input.setText("AlicePassword123!")
    login.login_button.click()

    dashboard = controller.current_window
    dashboard.task_table.selectRow(0)
    dashboard.status_combo.setCurrentIndex(1)
    dashboard.update_status_button.click()

    with controller.session_factory() as session:
        task = session.get(Task, task_id)
        assert task.status == "in_progress"

    assert dashboard.task_table.item(0, 3).text() == "in_progress"

    controller.shutdown()


def test_status_update_does_not_change_other_users_tasks(
    qtbot, tmp_path
):
    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'status_security.db').as_posix()}"
        )
    )

    controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )
    controller.auth_service.login(
        "admin", "AdminPassword123!"
    )

    from app.services.user_management import UserManagementService
    from app.models import Task

    users = UserManagementService(
        controller.session_factory,
        controller.auth_service,
    )

    alice_id = users.create_user(
        "alice", "AlicePassword123!"
    )
    bob_id = users.create_user(
        "bob", "BobPassword123!"
    )

    alice_task_id = controller.task_service.create_task(
        "Alice task", "Description", alice_id
    )
    bob_task_id = controller.task_service.create_task(
        "Bob task", "Description", bob_id
    )

    controller.auth_service.logout()
    controller.start()

    login = controller.current_window
    login.username_input.setText("alice")
    login.password_input.setText("AlicePassword123!")
    login.login_button.click()

    dashboard = controller.current_window

    assert dashboard.task_table.rowCount() == 1

    dashboard.task_table.selectRow(0)
    dashboard.status_combo.setCurrentIndex(2)
    dashboard.update_status_button.click()

    with controller.session_factory() as session:
        assert session.get(Task, alice_task_id).status == "completed"
        assert session.get(Task, bob_task_id).status == "to_do"

    controller.shutdown()
def test_admin_can_create_user_through_dialog(qtbot, tmp_path):
    from sqlalchemy import select

    from app.models.user import User

    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'create_user_gui.db').as_posix()}"
        )
    )

    controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )

    controller.start()

    login = controller.current_window
    login.username_input.setText("admin")
    login.password_input.setText("AdminPassword123!")
    login.login_button.click()

    dashboard = controller.current_window
    dashboard.create_user_button.click()

    dialog = controller.active_dialog

    assert dialog.isVisible()

    dialog.username_input.setText("alice")
    dialog.password_input.setText("AlicePassword123!")
    dialog.confirm_password_input.setText("AlicePassword123!")
    dialog.create_button.click()

    with controller.session_factory() as session:
        alice = session.scalar(
            select(User).where(User.username == "alice")
        )

        assert alice is not None
        assert alice.role == "user"

    assert not dialog.isVisible()

    controller.shutdown()

def test_admin_can_create_task_through_dialog(qtbot, tmp_path):
    from app.models.task import Task

    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'create_task_gui.db').as_posix()}"
        )
    )

    controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )
    controller.auth_service.login(
        "admin", "AdminPassword123!"
    )

    alice_id = controller.user_management_service.create_user(
        "alice", "AlicePassword123!"
    )

    controller.auth_service.logout()
    controller.start()

    login = controller.current_window
    login.username_input.setText("admin")
    login.password_input.setText("AdminPassword123!")
    login.login_button.click()

    dashboard = controller.current_window
    dashboard.create_task_button.click()

    dialog = controller.active_dialog

    assert dialog.isVisible()
    assert dialog.assigned_user_combo.count() == 1

    dialog.title_input.setText("Prepare presentation")
    dialog.description_input.setPlainText(
        "Create slides for the university project"
    )
    dialog.assigned_user_combo.setCurrentIndex(0)
    dialog.save_button.click()

    with controller.session_factory() as session:
        tasks = session.query(Task).all()

        assert len(tasks) == 1
        assert tasks[0].title == "Prepare presentation"
        assert tasks[0].assigned_user_id == alice_id
        assert tasks[0].status == "to_do"

    assert dashboard.task_table.rowCount() == 1
    assert not dialog.isVisible()

    controller.shutdown()
def test_admin_can_create_task_with_deadline(qtbot, tmp_path):
    from datetime import datetime
    from app.models.task import Task

    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'task_deadline.db').as_posix()}"
        )
    )

    controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )
    controller.auth_service.login(
        "admin", "AdminPassword123!"
    )

    controller.user_management_service.create_user(
        "alice", "AlicePassword123!"
    )

    controller.auth_service.logout()
    controller.start()

    login = controller.current_window
    login.username_input.setText("admin")
    login.password_input.setText("AdminPassword123!")
    login.login_button.click()

    dashboard = controller.current_window
    dashboard.create_task_button.click()

    dialog = controller.active_dialog
    dialog.title_input.setText("Submit coursework")
    dialog.description_input.setPlainText(
        "Submit the final report"
    )
    dialog.deadline_checkbox.setChecked(True)

    from PySide6.QtCore import QDate
    dialog.deadline_input.setDate(QDate(2026, 12, 15))

    dialog.save_button.click()

    with controller.session_factory() as session:
        task = session.query(Task).one()
        assert task.deadline is not None
        assert task.deadline.year == 2026
        assert task.deadline.month == 12
        assert task.deadline.day == 15

    assert not dialog.isVisible()
    controller.shutdown()

def test_admin_edit_button_opens_existing_task(qtbot, tmp_path):
    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'edit_task_gui.db').as_posix()}"
        )
    )

    controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )
    controller.auth_service.login(
        "admin", "AdminPassword123!"
    )

    alice_id = controller.user_management_service.create_user(
        "alice", "AlicePassword123!"
    )

    controller.task_service.create_task(
        "Original title",
        "Original description",
        alice_id,
    )

    controller.auth_service.logout()
    controller.start()

    login = controller.current_window
    login.username_input.setText("admin")
    login.password_input.setText("AdminPassword123!")
    login.login_button.click()

    dashboard = controller.current_window
    dashboard.task_table.selectRow(0)
    dashboard.edit_task_button.click()

    dialog = controller.active_dialog

    assert dialog.isVisible()
    assert dialog.title_input.text() == "Original title"
    assert (
        dialog.description_input.toPlainText()
        == "Original description"
    )

    controller.shutdown()
def test_admin_can_edit_and_reassign_task(qtbot, tmp_path):
    from app.models.task import Task

    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'edit_and_reassign.db').as_posix()}"
        )
    )

    controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )
    controller.auth_service.login(
        "admin", "AdminPassword123!"
    )

    alice_id = controller.user_management_service.create_user(
        "alice", "AlicePassword123!"
    )
    bob_id = controller.user_management_service.create_user(
        "bob", "BobPassword123!"
    )

    task_id = controller.task_service.create_task(
        "Original title",
        "Original description",
        alice_id,
    )

    controller.auth_service.logout()
    controller.start()

    login = controller.current_window
    login.username_input.setText("admin")
    login.password_input.setText("AdminPassword123!")
    login.login_button.click()

    dashboard = controller.current_window
    dashboard.task_table.selectRow(0)
    dashboard.edit_task_button.click()

    dialog = controller.active_dialog

    dialog.title_input.setText("Updated title")
    dialog.description_input.setPlainText(
        "Updated description"
    )

    bob_index = dialog.assigned_user_combo.findData(bob_id)
    assert bob_index >= 0
    dialog.assigned_user_combo.setCurrentIndex(bob_index)

    dialog.save_button.click()

    with controller.session_factory() as session:
        task = session.get(Task, task_id)

        assert task.title == "Updated title"
        assert task.description == "Updated description"
        assert task.assigned_user_id == bob_id

    assert dashboard.task_table.item(0, 1).text() == "Updated title"
    assert not dialog.isVisible()

    controller.shutdown()
def test_invalid_reassignment_does_not_partially_edit_task(
    qtbot, tmp_path
):
    from app.models.task import Task

    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'invalid_edit.db').as_posix()}"
        )
    )

    controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )
    controller.auth_service.login(
        "admin", "AdminPassword123!"
    )

    alice_id = controller.user_management_service.create_user(
        "alice", "AlicePassword123!"
    )

    task_id = controller.task_service.create_task(
        "Original title",
        "Original description",
        alice_id,
    )

    controller.auth_service.logout()
    controller.start()

    login = controller.current_window
    login.username_input.setText("admin")
    login.password_input.setText("AdminPassword123!")
    login.login_button.click()

    dashboard = controller.current_window
    dashboard.task_table.selectRow(0)
    dashboard.edit_task_button.click()

    dialog = controller.active_dialog

    controller._handle_edit_task(
        task_id,
        {
            "title": "Should not be saved",
            "description": "Should not be saved",
            "assigned_user_id": 999999,
            "deadline": None,
        },
    )

    with controller.session_factory() as session:
        task = session.get(Task, task_id)

        assert task.title == "Original title"
        assert task.description == "Original description"
        assert task.assigned_user_id == alice_id

    assert dialog.isVisible()
    controller.shutdown()

def test_admin_can_edit_task_deadline(qtbot, tmp_path):
    from datetime import datetime
    from PySide6.QtCore import QDate
    from app.models.task import Task

    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'edit_deadline.db').as_posix()}"
        )
    )

    controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )
    controller.auth_service.login(
        "admin", "AdminPassword123!"
    )

    alice_id = controller.user_management_service.create_user(
        "alice", "AlicePassword123!"
    )

    task_id = controller.task_service.create_task(
        "Submit report",
        "Coursework deadline",
        alice_id,
        deadline=datetime(2026, 11, 10),
    )

    controller.auth_service.logout()
    controller.start()

    login = controller.current_window
    login.username_input.setText("admin")
    login.password_input.setText("AdminPassword123!")
    login.login_button.click()

    dashboard = controller.current_window
    dashboard.task_table.selectRow(0)
    dashboard.edit_task_button.click()

    dialog = controller.active_dialog

    assert dialog.deadline_checkbox.isChecked()

    dialog.deadline_input.setDate(QDate(2026, 12, 15))
    dialog.save_button.click()

    with controller.session_factory() as session:
        task = session.get(Task, task_id)

        assert task.deadline is not None
        assert task.deadline.year == 2026
        assert task.deadline.month == 12
        assert task.deadline.day == 15

    assert not dialog.isVisible()
    controller.shutdown()

def test_admin_can_confirm_task_deletion(qtbot, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    from app.models.task import Task

    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'confirm_delete.db').as_posix()}"
        )
    )

    controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )
    controller.auth_service.login(
        "admin", "AdminPassword123!"
    )

    alice_id = controller.user_management_service.create_user(
        "alice", "AlicePassword123!"
    )

    task_id = controller.task_service.create_task(
        "Task to delete", "Description", alice_id
    )

    controller.auth_service.logout()
    controller.start()

    login = controller.current_window
    login.username_input.setText("admin")
    login.password_input.setText("AdminPassword123!")
    login.login_button.click()

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )

    dashboard = controller.current_window
    dashboard.task_table.selectRow(0)
    dashboard.delete_task_button.click()

    with controller.session_factory() as session:
        assert session.get(Task, task_id) is None

    assert dashboard.task_table.rowCount() == 0

    controller.shutdown()

def test_admin_can_cancel_task_deletion(qtbot, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    from app.models.task import Task

    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'cancel_delete.db').as_posix()}"
        )
    )

    controller.setup_service.create_initial_admin(
        "admin", "AdminPassword123!"
    )
    controller.auth_service.login(
        "admin", "AdminPassword123!"
    )

    alice_id = controller.user_management_service.create_user(
        "alice", "AlicePassword123!"
    )

    task_id = controller.task_service.create_task(
        "Keep this task", "Description", alice_id
    )

    controller.auth_service.logout()
    controller.start()

    login = controller.current_window
    login.username_input.setText("admin")
    login.password_input.setText("AdminPassword123!")
    login.login_button.click()

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )

    dashboard = controller.current_window
    dashboard.task_table.selectRow(0)
    dashboard.delete_task_button.click()

    with controller.session_factory() as session:
        assert session.get(Task, task_id) is not None

    assert dashboard.task_table.rowCount() == 1

    controller.shutdown()


def test_initial_admin_setup_cannot_be_repeated(qtbot, tmp_path):
    from app.models.user import User
    from app.services.setup import SetupError

    controller = AppController(
        database_url=(
            f"sqlite:///{(tmp_path / 'repeat_setup.db').as_posix()}"
        )
    )

    # Initially, the application requires administrator setup.
    controller.start()

    setup_window = controller.current_window
    assert setup_window.windowTitle() == (
        "Task Manager - Initial Setup"
    )

    # Complete the initial setup through the GUI.
    setup_window.username_input.setText("admin")
    setup_window.password_input.setText("AdminPassword123!")
    setup_window.confirm_password_input.setText(
        "AdminPassword123!"
    )
    setup_window.create_button.click()

    # Successful setup takes the user to the login window.
    assert controller.current_window.windowTitle() == (
        "Task Manager - Login"
    )
    assert not controller.setup_service.setup_required()

    # Attempting to run initial setup again must be rejected.
    try:
        controller.setup_service.create_initial_admin(
            "second_admin",
            "SecondAdminPassword123!",
        )
    except SetupError:
        pass
    else:
        raise AssertionError(
            "Initial administrator setup was allowed twice."
        )

    # Verify that the rejected attempt created no extra account.
    with controller.session_factory() as session:
        accounts = session.query(User).all()

        assert len(accounts) == 1
        assert accounts[0].username == "admin"
        assert accounts[0].role == "admin"

    controller.shutdown()

