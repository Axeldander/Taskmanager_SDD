
from sqlalchemy import select, func
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


    def _require_authenticated_user(self, session):
        current_user = self.auth_service.current_user

        if current_user is None:
            raise TaskManagementError("You must be logged in.")

        user = session.get(User, current_user.id)

        if user is None or user.role != current_user.role:
            raise TaskManagementError(
                "Authentication is no longer valid."
            )

        if user.role not in ("admin", "user"):
            raise TaskManagementError(
                "Unrecognized account role."
            )

        return user

    def get_tasks(self):
        with self.session_factory() as session:
            user = self._require_authenticated_user(session)

            query = select(Task).order_by(Task.id)

            if user.role == "user":
                query = query.where(
                    Task.assigned_user_id == user.id
                )

            return list(session.scalars(query).all())

    def update_status(self, task_id: int, new_status: str):
        allowed_statuses = {
            "to_do",
            "in_progress",
            "completed",
        }

        with self.session_factory() as session:
            user = self._require_authenticated_user(session)

            if user.role != "user":
                raise TaskManagementError(
                    "Only standard users can update task status."
                )

            if (
                not isinstance(new_status, str)
                or new_status not in allowed_statuses
            ):
                raise TaskManagementError("Invalid task status.")

            task = session.get(Task, task_id)

            if task is None:
                raise TaskManagementError("Task does not exist.")

            if task.assigned_user_id != user.id:
                raise TaskManagementError(
                    "You cannot modify another user's task."
                )

            task.status = new_status
            session.commit()

    def get_status_summary(self):
        with self.session_factory() as session:
            self._require_admin(session)

            results = session.execute(
                select(Task.status, func.count(Task.id))
                .group_by(Task.status)
            ).all()

            summary = {
                "to_do": 0,
                "in_progress": 0,
                "completed": 0,
            }

            for status, count in results:
                summary[status] = count

            return summary

    def edit_task(self, task_id: int, title=None, description=None):
        """Allow administrators to edit task details."""

        with self.session_factory() as session:
            self._require_admin(session)

            task = session.get(Task, task_id)

            if task is None:
                raise TaskManagementError("Task does not exist.")

            if title is not None:
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

                task.title = title

            if description is not None:
                if not isinstance(description, str):
                    raise TaskManagementError(
                        "Task description must be a string."
                    )

                task.description = description

            session.commit()

    def reassign_task(self, task_id: int, new_user_id: int):
        """Allow administrators to reassign a task."""

        with self.session_factory() as session:
            self._require_admin(session)

            task = session.get(Task, task_id)

            if task is None:
                raise TaskManagementError("Task does not exist.")

            if isinstance(new_user_id, bool) or not isinstance(
                new_user_id, int
            ):
                raise TaskManagementError(
                    "Assigned user ID must be an integer."
                )

            user = session.get(User, new_user_id)

            if user is None:
                raise TaskManagementError(
                    "Assigned user does not exist."
                )

            if user.role != "user":
                raise TaskManagementError(
                    "Tasks can only be assigned to standard users."
                )

            task.assigned_user_id = new_user_id
            session.commit()

    def delete_task(self, task_id: int):
        """Allow administrators to delete a task."""

        with self.session_factory() as session:
            self._require_admin(session)

            task = session.get(Task, task_id)

            if task is None:
                raise TaskManagementError("Task does not exist.")

            session.delete(task)
            session.commit()
