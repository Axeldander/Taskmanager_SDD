
from app.database.connection import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from app.services.auth import AuthenticationService
from app.services.setup import SetupService
from app.services.task_management import TaskManagementService

from app.gui.login_window import LoginWindow
from app.gui.setup_window import SetupWindow
from app.gui.admin_dashboard import AdminDashboard
from app.gui.user_dashboard import UserDashboard
from app.gui.create_user_dialog import CreateUserDialog
from app.services.user_management import UserManagementService
from sqlalchemy import select
from PySide6.QtWidgets import QMessageBox
from app.models.user import User
from app.gui.task_dialog import TaskDialog
from app.services.task_management import TaskManagementError

from datetime import datetime
from sqlalchemy import select
from app.models.user import User

class AppController:
    def __init__(self, database_url=None):
        self.engine = create_database_engine(database_url)
        initialize_database(self.engine)

        self.session_factory = create_session_factory(
            self.engine
        )

        self.auth_service = AuthenticationService(
            self.session_factory
        )
        self.setup_service = SetupService(
            self.session_factory
        )
        self.task_service = TaskManagementService(
            self.session_factory,
            self.auth_service,
        )
        self.user_management_service = UserManagementService(
            self.session_factory,
            self.auth_service,
        )

        self.active_dialog = None

        self.current_window = None

    def start(self):
        if self.setup_service.setup_required():
            self._show_setup()
        else:
            self._show_login()

    def _change_window(self, new_window):
        old_window = self.current_window
        self.current_window = new_window

        new_window.show()

        if old_window is not None:
            old_window.close()

    def _show_setup(self):
        window = SetupWindow()
        window.setup_requested.connect(
            self._handle_setup
        )
        self._change_window(window)

    def _handle_setup(self, username, password):
        try:
            self.setup_service.create_initial_admin(
                username, password
            )
        except Exception as exc:
            self.current_window.show_error(
                str(exc)
            )
            return

        self._show_login()

    def _show_login(self):
        window = LoginWindow()
        window.login_requested.connect(
            self._handle_login
        )
        self._change_window(window)


    def _handle_login(self, username, password):
        user = self.auth_service.login(username, password)

        if user is None:
            self.current_window.show_error(
                "Incorrect username or password. Please try again."
            )
            return

        if user.role == "admin":
            self._show_admin_dashboard()
        else:
            self._show_user_dashboard()

    def _show_admin_dashboard(self):
        window = AdminDashboard()

        window.logout_requested.connect(self._handle_logout)
        window.refresh_requested.connect(
            self._refresh_admin_dashboard
        )
        window.create_user_requested.connect(
            self._show_create_user_dialog
        )
        window.create_task_requested.connect(
            self._show_create_task_dialog
        )
        window.edit_task_requested.connect(
            self._show_edit_task_dialog
        )
        window.delete_task_requested.connect(
            self._handle_delete_task
        )

        self._change_window(window)
        self._refresh_admin_dashboard()

    def _refresh_admin_dashboard(self):
        tasks = self.task_service.get_tasks()

        with self.session_factory() as session:
            users = session.scalars(
                select(User).where(User.role == "user")
            ).all()

            usernames = {
                user.id: user.username
                for user in users
            }

        rows = []

        for task in tasks:
            rows.append({
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "assigned_user": usernames.get(
                    task.assigned_user_id,
                    "Unknown user",
                ),
                "deadline": task.deadline,
            })

        self.current_window.display_tasks(rows)

        summary = self.task_service.get_status_summary()
        self.current_window.display_status_summary(summary)

    def _show_create_user_dialog(self):
        dialog = CreateUserDialog(self.current_window)

        dialog.create_user_requested.connect(
            self._handle_create_user
        )

        self.active_dialog = dialog
        dialog.show()

    def _handle_create_user(self, username, password):
        from app.services.user_management import UserManagementError

        dialog = self.active_dialog

        if dialog.password_input.text() != (
            dialog.confirm_password_input.text()
        ):
            dialog.show_error("Passwords do not match.")
            return

        try:
            self.user_management_service.create_user(
                username, password
            )
        except UserManagementError as exc:
            dialog.show_error(str(exc))
            return

        dialog.accept()
        self.active_dialog = None
        self._refresh_admin_dashboard()


    def _show_create_task_dialog(self):
        dialog = TaskDialog()

        with self.session_factory() as session:
            users = session.scalars(
                select(User).where(User.role == "user")
            ).all()

            user_options = [
                (user.id, user.username)
                for user in users
            ]

        dialog.set_users(user_options)

        dialog.task_saved.connect(
            self._handle_create_task
        )

        self.active_dialog = dialog
        dialog.show()

    def _handle_create_task(self, task_data):
        dialog = self.active_dialog

        try:
            deadline = task_data["deadline"]

            if deadline is not None:
                deadline = datetime.fromisoformat(deadline)

            self.task_service.create_task(
                title=task_data["title"],
                description=task_data["description"],
                assigned_user_id=task_data["assigned_user_id"],
                deadline=deadline,
            )
        except (TaskManagementError, ValueError, TypeError) as exc:
            dialog.show_error(str(exc))
            return

        dialog.accept()
        self.active_dialog = None
        self._refresh_admin_dashboard()
    def _show_edit_task_dialog(self, task_id):
        from app.models.task import Task

        with self.session_factory() as session:
            task = session.get(Task, task_id)

            if task is None:
                return

            task_data = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "assigned_user_id": task.assigned_user_id,
                "deadline": task.deadline,
            }

            users = session.scalars(
                select(User).where(User.role == "user")
            ).all()

            user_options = [
                (user.id, user.username)
                for user in users
            ]

        dialog = TaskDialog(task_id=task_id)
        dialog.set_users(user_options)
        dialog.load_task(task_data)

        dialog.task_saved.connect(
            lambda task_data: self._handle_edit_task(
                task_id, task_data
            )
        )

        self.active_dialog = dialog
        dialog.show()
    def _handle_edit_task(self, task_id, task_data):
        dialog = self.active_dialog

        try:
            with self.session_factory() as session:
                assignee = session.get(
                    User,
                    task_data["assigned_user_id"],
                )

                if assignee is None or assignee.role != "user":
                    dialog.show_error(
                        "Please select a valid standard user."
                    )
                    return

            deadline = task_data["deadline"]

            if deadline is not None:
                deadline = datetime.fromisoformat(deadline)

            self.task_service.update_task_details(
                task_id,
                title=task_data["title"],
                description=task_data["description"],
                assigned_user_id=task_data["assigned_user_id"],
                deadline=deadline,
            )


        except (TaskManagementError, ValueError, TypeError) as exc:
            dialog.show_error(str(exc))
            return

        dialog.accept()
        self.active_dialog = None
        self._refresh_admin_dashboard()


    def _handle_delete_task(self, task_id):
        answer = QMessageBox.question(
            self.current_window,
            "Confirm Task Deletion",
            "Are you sure you want to delete this task?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.task_service.delete_task(task_id)
        except TaskManagementError as exc:
            QMessageBox.warning(
                self.current_window,
                "Unable to Delete Task",
                str(exc),
            )
            return

        self._refresh_admin_dashboard()

    def _show_user_dashboard(self):
        window = UserDashboard()
        window.logout_requested.connect(self._handle_logout)
        window.refresh_requested.connect(
            self._refresh_user_dashboard
        )
        window.status_update_requested.connect(
            self._handle_status_update
        )
        self._change_window(window)
        self._refresh_user_dashboard()

    def _refresh_user_dashboard(self):
        tasks = self.task_service.get_tasks()

        rows = []

        for task in tasks:
            rows.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "deadline": task.deadline,
            })

        self.current_window.display_tasks(rows)

    def _handle_status_update(self, task_id, new_status):
        """Save a user's task status change and refresh the table."""
        from app.services.task_management import TaskManagementError

        try:
            self.task_service.update_status(
                task_id, new_status
            )
        except TaskManagementError as exc:
            self.current_window.error_label.setText(
                str(exc)
            )
            return

        self.current_window.error_label.clear()
        self._refresh_user_dashboard()


    def _handle_logout(self):
        self.auth_service.logout()
        self._show_login()

    def shutdown(self):
        if self.current_window is not None:
            self.current_window.close()
            self.current_window = None

        self.auth_service.logout()
        self.engine.dispose()
