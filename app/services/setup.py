
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import User
from app.services.passwords import hash_password


class SetupError(Exception):
    """Raised when initial administrator setup cannot be completed."""


class SetupService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def setup_required(self) -> bool:
        """Return True if no administrator account exists."""
        with self.session_factory() as session:
            admin_id = session.scalar(
                select(User.id)
                .where(User.role == "admin")
                .limit(1)
            )
            return admin_id is None

    def create_initial_admin(
        self,
        username: str,
        password: str,
    ) -> int:
        """Create the first administrator exactly once."""

        if not isinstance(username, str):
            raise SetupError("Username must be a string.")

        username = username.strip()

        if not username:
            raise SetupError("Username cannot be empty.")

        if len(username) > 100:
            raise SetupError("Username cannot exceed 100 characters.")

        try:
            password_hash = hash_password(password)
        except ValueError as exc:
            raise SetupError(str(exc)) from exc

        with self.session_factory() as session:
            try:
                # Acquire the SQLite write lock before checking for an
                # existing administrator. This prevents two concurrent
                # setup attempts from both passing the check.
                if session.bind.dialect.name == "sqlite":
                    session.connection().exec_driver_sql(
                        "BEGIN IMMEDIATE"
                    )

                existing_admin = session.scalar(
                    select(User.id)
                    .where(User.role == "admin")
                    .limit(1)
                )

                if existing_admin is not None:
                    raise SetupError(
                        "Initial administrator setup has already been completed."
                    )

                existing_username = session.scalar(
                    select(User.id)
                    .where(User.username == username)
                    .limit(1)
                )

                if existing_username is not None:
                    raise SetupError(
                        "This username is already in use."
                    )

                admin = User(
                    username=username,
                    password_hash=password_hash,
                    role="admin",
                )

                session.add(admin)
                session.commit()

                return admin.id

            except IntegrityError as exc:
                session.rollback()
                raise SetupError(
                    "Administrator setup failed because the account "
                    "could not be saved."
                ) from exc

            except Exception:
                session.rollback()
                raise
