
import pytest

from app.database.connection import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from app.models import User
from app.services.auth import AuthenticationService
from app.services.passwords import hash_password


@pytest.fixture
def auth_environment(tmp_path):
    database_path = tmp_path / "auth.db"
    database_url = f"sqlite:///{database_path.as_posix()}"

    engine = create_database_engine(database_url)
    initialize_database(engine)

    session_factory = create_session_factory(engine)

    with session_factory() as session:
        admin = User(
            username="admin",
            password_hash=hash_password("AdminPassword123!"),
            role="admin",
        )

        standard_user = User(
            username="alice",
            password_hash=hash_password("AlicePassword123!"),
            role="user",
        )

        session.add_all([admin, standard_user])
        session.commit()

    service = AuthenticationService(session_factory)

    yield service

    engine.dispose()


def test_admin_can_log_in(auth_environment):
    user = auth_environment.login(
        "admin", "AdminPassword123!"
    )

    assert user is not None
    assert user.username == "admin"
    assert user.role == "admin"
    assert auth_environment.is_authenticated()
    assert auth_environment.is_admin()


def test_standard_user_can_log_in(auth_environment):
    user = auth_environment.login(
        "alice", "AlicePassword123!"
    )

    assert user is not None
    assert user.role == "user"
    assert auth_environment.is_admin() is False


def test_wrong_password_is_rejected(auth_environment):
    result = auth_environment.login(
        "admin", "WrongPassword123!"
    )

    assert result is None
    assert auth_environment.is_authenticated() is False


def test_unknown_username_is_rejected(auth_environment):
    result = auth_environment.login(
        "unknown", "SomePassword123!"
    )

    assert result is None
    assert auth_environment.is_authenticated() is False


def test_logout_clears_authentication(auth_environment):
    auth_environment.login(
        "admin", "AdminPassword123!"
    )

    auth_environment.logout()

    assert auth_environment.current_user is None
    assert auth_environment.is_authenticated() is False
    assert auth_environment.is_admin() is False


def test_failed_login_clears_previous_session(auth_environment):
    auth_environment.login(
        "admin", "AdminPassword123!"
    )

    result = auth_environment.login(
        "admin", "WrongPassword123!"
    )

    assert result is None
    assert auth_environment.is_authenticated() is False
