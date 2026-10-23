
import pytest

from sqlalchemy import select

from app.database.connection import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from app.models import Task, User
from app.services.auth import AuthenticationService
from app.services.passwords import hash_password
from app.services.task_management import (
    TaskManagementService,
    TaskManagementError,
)


@pytest.fixture
def environment(tmp_path):
    database_path = tmp_path / "task_management.db"
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
        alice = User(
            username="alice",
            password_hash=hash_password("AlicePassword123!"),
            role="user",
        )
        bob = User(
            username="bob",
            password_hash=hash_password("BobPassword123!"),
            role="user",
        )

        session.add_all([admin, alice, bob])
        session.commit()

        alice_id = alice.id
        bob_id = bob.id
        admin_id = admin.id

    auth = AuthenticationService(session_factory)
    management = TaskManagementService(session_factory, auth)

    yield auth, management, session_factory, {
        "admin": admin_id,
        "alice": alice_id,
        "bob": bob_id,
    }

    engine.dispose()


def test_admin_can_create_and_assign_task(environment):
    auth, management, session_factory, ids = environment

    auth.login("admin", "AdminPassword123!")

    task_id = management.create_task(
        title="Prepare report",
        description="Complete the project report",
        assigned_user_id=ids["alice"],
    )

    with session_factory() as session:
        task = session.get(Task, task_id)

        assert task is not None
        assert task.title == "Prepare report"
        assert task.description == "Complete the project report"
        assert task.assigned_user_id == ids["alice"]
        assert task.status == "to_do"


def test_standard_user_cannot_create_task(environment):
    auth, management, session_factory, ids = environment

    auth.login("alice", "AlicePassword123!")

    with pytest.raises(TaskManagementError):
        management.create_task(
            title="Unauthorized task",
            description="Should not be created",
            assigned_user_id=ids["bob"],
        )

    with session_factory() as session:
        task = session.scalar(
            select(Task).where(Task.title == "Unauthorized task")
        )
        assert task is None


def test_logged_out_user_cannot_create_task(environment):
    _, management, _, ids = environment

    with pytest.raises(TaskManagementError):
        management.create_task(
            title="Unauthorized task",
            description="Should not be created",
            assigned_user_id=ids["alice"],
        )


def test_task_cannot_be_assigned_to_admin(environment):
    auth, management, _, ids = environment

    auth.login("admin", "AdminPassword123!")

    with pytest.raises(TaskManagementError):
        management.create_task(
            title="Invalid assignment",
            description="Admins cannot be task assignees",
            assigned_user_id=ids["admin"],
        )


def test_task_cannot_be_assigned_to_unknown_user(environment):
    auth, management, _, _ = environment

    auth.login("admin", "AdminPassword123!")

    with pytest.raises(TaskManagementError):
        management.create_task(
            title="Invalid assignment",
            description="User does not exist",
            assigned_user_id=999999,
        )


def test_empty_task_title_is_rejected(environment):
    auth, management, _, ids = environment

    auth.login("admin", "AdminPassword123!")

    with pytest.raises(TaskManagementError):
        management.create_task(
            title="   ",
            description="A task without a title",
            assigned_user_id=ids["alice"],
        )


def test_task_title_over_200_characters_is_rejected(environment):
    auth, management, _, ids = environment

    auth.login("admin", "AdminPassword123!")

    with pytest.raises(TaskManagementError):
        management.create_task(
            title="x" * 201,
            description="Title is too long",
            assigned_user_id=ids["alice"],
        )
