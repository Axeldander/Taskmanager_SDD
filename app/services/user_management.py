
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import User
from app.services.passwords import hash_password


class UserManagementError(Exception):
    """Raised when account creation is not permitted or fails."""


class UserManagementService:
    def __init__(self, session_factory, auth_service):
        self.session_factory = session_factory
        self.auth_service = auth_service

    def create_user(
        self,
        username: str,
        password: str,
    ) -> int:
        """Create a standard-user account as an administrator."""

        # Authorization must be enforced in the service layer.
        if not self.auth_service.is_admin():
            raise UserManagementError(
                "Only administrators can create user accounts."
            )

        # Validate username.
        if not isinstance(username, str):
            raise UserManagementError(
                "Username must be a string."
            )

        username = username.strip()

        if not username:
            raise UserManagementError(
                "Username cannot be empty."
            )

        if len(username) > 100:
            raise UserManagementError(
                "Username cannot exceed 100 characters."
            )

        # Validate and hash password.
        try:
            password_hash = hash_password(password)
        except ValueError as exc:
            raise UserManagementError(str(exc)) from exc

        with self.session_factory() as session:
            try:
                # Ensure the authenticated administrator still exists
                # and still has administrator privileges.
                current_user = self.auth_service.current_user

                admin = session.get(User, current_user.id)

                if admin is None or admin.role != "admin":
                    raise UserManagementError(
                        "Administrator privileges are no longer valid."
                    )

                existing_user = session.scalar(
                    select(User.id)
                    .where(User.username == username)
                    .limit(1)
                )

                if existing_user is not None:
                    raise UserManagementError(
                        "This username is already in use."
                    )

                new_user = User(
                    username=username,
                    password_hash=password_hash,
                    role="user",
                )

                session.add(new_user)
                session.commit()

                return new_user.id

            except IntegrityError as exc:
                session.rollback()
                raise UserManagementError(
                    "Account creation failed. "
                    "The username may already exist."
                ) from exc

            except Exception:
                session.rollback()
                raise
