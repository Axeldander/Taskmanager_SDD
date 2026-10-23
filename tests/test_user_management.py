
import pytest

from sqlalchemy import select

from app.database.connection import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from app.models import User
from app.services.auth import AuthenticationService
from app.services.passwords import hash_password, verify_password
from app.services.user_management import (
    UserManagementService,
    UserManagementError,
)


@pytest.fixture
def environment(tmp_path):
    database_path = tmp_path / "users.db"
    database_url = f"sqlite:///{database_path.as_posix()}"

    engine = create_database_engine(database_url)
    initialize_database(engine)

    session_factory = create_session_factory(engine)

    with session_factory() as session:
        session.add_all([
            User(
                username="admin",
                password_hash=hash_password("AdminPassword123!"),
                role="admin",
            ),
            User(
                username="alice",
                password_hash=hash_password("AlicePassword123!"),
                role="user",
            ),
        ])
        session.commit()

    auth = AuthenticationService(session_factory)
    management = UserManagementService(session_factory, auth)

    yield auth, management, session_factory

    engine.dispose()


def test_admin_can_create_standard_user(environment):
    auth, management, session_factory = environment

    auth.login("admin", "AdminPassword123!")

    new_user_id = management.create_user(
        "bob",
        "SecurePassword123!",
    )

    with session_factory() as session:
        user = session.get(User, new_user_id)

        assert user is not None
        assert user.username == "bob"
        assert user.role == "user"
        assert user.password_hash != "SecurePassword123!"
        assert verify_password(
            user.password_hash,
            "SecurePassword123!",
        )


def test_standard_user_cannot_create_account(environment):
    auth, management, session_factory = environment

    auth.login("alice", "AlicePassword123!")

    with pytest.raises(UserManagementError):
        management.create_user(
            "bob",
            "SecurePassword123!",
        )

    with session_factory() as session:
        assert session.scalar(
            select(User).where(User.username == "bob")
        ) is None


def test_logged_out_user_cannot_create_account(environment):
    auth, management, _ = environment

    with pytest.raises(UserManagementError):
        management.create_user(
            "bob",
            "SecurePassword123!",
        )


def test_duplicate_username_is_rejected(environment):
    auth, management, _ = environment

    auth.login("admin", "AdminPassword123!")

    with pytest.raises(UserManagementError):
        management.create_user(
            "alice",
            "SecurePassword123!",
        )


def test_empty_username_is_rejected(environment):
    auth, management, _ = environment

    auth.login("admin", "AdminPassword123!")

    with pytest.raises(UserManagementError):
        management.create_user(
            "   ",
            "SecurePassword123!",
        )


def test_username_over_100_characters_is_rejected(environment):
    auth, management, _ = environment

    auth.login("admin", "AdminPassword123!")

    with pytest.raises(UserManagementError):
        management.create_user(
            "a" * 101,
            "SecurePassword123!",
        )


def test_short_password_is_rejected(environment):
    auth, management, _ = environment

    auth.login("admin", "AdminPassword123!")

    with pytest.raises(UserManagementError):
        management.create_user(
            "bob",
            "short",
        )


def test_failed_creation_does_not_save_user(environment):
    auth, management, session_factory = environment

    auth.login("admin", "AdminPassword123!")

    with pytest.raises(UserManagementError):
        management.create_user(
            "bob",
            "short",
        )

    with session_factory() as session:
        assert session.scalar(
            select(User).where(User.username == "bob")
        ) is None


def test_logout_revokes_account_creation_permission(environment):
    auth, management, _ = environment

    auth.login("admin", "AdminPassword123!")
    auth.logout()

    with pytest.raises(UserManagementError):
        management.create_user(
            "bob",
            "SecurePassword123!",
        )
