
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.services.passwords import verify_password


@dataclass(frozen=True)
class AuthenticatedUser:
    id: int
    username: str
    role: str


class AuthenticationService:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.current_user = None

    def login(self, username: str, password: str):
        """Authenticate a user and establish the active identity."""

        # A failed login must never leave a previous user logged in.
        self.current_user = None

        if not isinstance(username, str) or not isinstance(password, str):
            return None

        with self.session_factory() as session:
            user = session.scalar(
                select(User).where(User.username == username)
            )

            if user is None:
                return None

            if not verify_password(user.password_hash, password):
                return None

            self.current_user = AuthenticatedUser(
                id=user.id,
                username=user.username,
                role=user.role,
            )

            return self.current_user

    def logout(self):
        """Clear the active authenticated identity."""
        self.current_user = None

    def is_authenticated(self):
        return self.current_user is not None

    def is_admin(self):
        return (
            self.current_user is not None
            and self.current_user.role == "admin"
        )
