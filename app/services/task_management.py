
from sqlalchemy.exc import IntegrityError

from app.models import Task, User


class TaskManagementError(Exception):
    """Raised when a task operation is invalid or unauthorized."""


class TaskManagementService:
    def __init__(self, session_factory, auth_service):
        self.session_factory = session_factory
        self.auth_service = auth_service

    def _require_admin(self, session):
        """Ensure the current user is still an administrator."""

        if not self.auth_service.is_admin():
            raise TaskManagementError(
                "Only administrators can perform this operation."
            )

        current_user = self.auth_service.current_user

        admin = session.get(User, current_user.id)

        if admin is None or admin.role != "admin":
            raise TaskManagementError(
                "Administrator privileges are no longer valid."
            )

    def create_task(
        self,
        title: str,
        description: str,
        assigned_user_id: int,
        deadline=None,
    ) -> int:
        """Create a task assigned to exactly one standard user."""

        with self.session_factory() as session:
            self._require_admin(session)

            if not isinstance(title, str):
                raise TaskManagementError(
                    "Task title must be a string."
                )

            title = title.strip()

            if not title:
                raise TaskManagementError(
                    "Task title cannot be empty."
                )

            if len(title) > 200:
                raise TaskManagementError(
                    "Task title cannot exceed 200 characters."
                )

            if not isinstance(description, str):
                raise TaskManagementError(
                    "Task description must be a string."
                )

            if (
                isinstance(assigned_user_id, bool)
                or not isinstance(assigned_user_id, int)
            ):
                raise TaskManagementError(
                    "Assigned user ID must be an integer."
                )

            assigned_user = session.get(
                User,
                assigned_user_id,
            )

            if assigned_user is None:
                raise TaskManagementError(
                    "Assigned user does not exist."
                )

            if assigned_user.role != "user":
                raise TaskManagementError(
                    "Tasks can only be assigned to standard users."
                )

            task = Task(
                title=title,
                description=description,
                assigned_user_id=assigned_user_id,
                deadline=deadline,
                status="to_do",
            )

            try:
                session.add(task)
                session.commit()
                return task.id

            except IntegrityError as exc:
                session.rollback()
                raise TaskManagementError(
                    "Task creation failed."
                ) from exc
