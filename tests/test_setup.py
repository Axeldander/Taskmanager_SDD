
import pytest

from sqlalchemy import select, func

from app.database.connection import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from app.models import User
from app.services.passwords import verify_password
from app.services.setup import SetupError, SetupService


@pytest.fixture
def setup_environment(tmp_path):
    database_path = tmp_path / "setup.db"
    database_url = f"sqlite:///{database_path.as_posix()}"

    engine = create_database_engine(database_url)
    initialize_database(engine)

    session_factory = create_session_factory(engine)
    setup_service = SetupService(session_factory)

    yield setup_service, session_factory

    engine.dispose()


def test_setup_required_for_empty_database(setup_environment):
    service, _ = setup_environment

    assert service.setup_required() is True


def test_initial_admin_can_be_created(setup_environment):
    service, session_factory = setup_environment

    admin_id = service.create_initial_admin(
        "admin",
        "SecureAdminPassword123!",
    )

    with session_factory() as session:
        admin = session.get(User, admin_id)

        assert admin is not None
        assert admin.username == "admin"
        assert admin.role == "admin"
        assert admin.password_hash != "SecureAdminPassword123!"
        assert verify_password(
            admin.password_hash,
            "SecureAdminPassword123!",
        )


def test_setup_not_required_after_admin_creation(setup_environment):
    service, _ = setup_environment

    service.create_initial_admin(
        "admin",
        "SecureAdminPassword123!",
    )

    assert service.setup_required() is False


def test_second_initial_admin_is_rejected(setup_environment):
    service, session_factory = setup_environment

    service.create_initial_admin(
        "admin",
        "SecureAdminPassword123!",
    )

    with pytest.raises(SetupError):
        service.create_initial_admin(
            "second_admin",
            "AnotherSecurePassword123!",
        )

    with session_factory() as session:
        admin_count = session.scalar(
            select(func.count())
            .select_from(User)
            .where(User.role == "admin")
        )

        assert admin_count == 1


def test_short_password_is_rejected(setup_environment):
    service, _ = setup_environment

    with pytest.raises(SetupError):
        service.create_initial_admin(
            "admin",
            "short",
        )

    assert service.setup_required() is True


def test_empty_username_is_rejected(setup_environment):
    service, _ = setup_environment

    with pytest.raises(SetupError):
        service.create_initial_admin(
            "   ",
            "SecureAdminPassword123!",
        )

    assert service.setup_required() is True


def test_duplicate_username_is_rejected(setup_environment):
    service, session_factory = setup_environment

    with session_factory() as session:
        session.add(
            User(
                username="taken",
                password_hash="test-hash",
                role="user",
            )
        )
        session.commit()

    with pytest.raises(SetupError):
        service.create_initial_admin(
            "taken",
            "SecureAdminPassword123!",
        )

    assert service.setup_required() is True


def test_failed_setup_does_not_create_admin(setup_environment):
    service, session_factory = setup_environment

    with pytest.raises(SetupError):
        service.create_initial_admin(
            "admin",
            "too-short",
        )

    with session_factory() as session:
        users = session.scalars(
            select(User).where(User.role == "admin")
        ).all()

        assert users == []

