
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

        ids = {
            "admin": admin.id,
            "alice": alice.id,
            "bob": bob.id,
        }

    auth = AuthenticationService(session_factory)
    management = TaskManagementService(session_factory, auth)

    yield auth, management, session_factory, ids

    engine.dispose()

def test_admin_can_view_all_tasks(environment):
    auth, management, _, ids = environment

    auth.login("admin", "AdminPassword123!")

    management.create_task("Alice task", "For Alice", ids["alice"])
    management.create_task("Bob task", "For Bob", ids["bob"])

    tasks = management.get_tasks()

    assert len(tasks) == 2


def test_user_sees_only_assigned_tasks(environment):
    auth, management, _, ids = environment

    auth.login("admin", "AdminPassword123!")

    management.create_task("Alice task", "For Alice", ids["alice"])
    management.create_task("Bob task", "For Bob", ids["bob"])

    auth.login("alice", "AlicePassword123!")

    tasks = management.get_tasks()

    assert len(tasks) == 1
    assert tasks[0].title == "Alice task"


def test_logged_out_user_cannot_view_tasks(environment):
    _, management, _, _ = environment

    with pytest.raises(TaskManagementError):
        management.get_tasks()


def test_user_can_update_own_task_status(environment):
    auth, management, session_factory, ids = environment

    auth.login("admin", "AdminPassword123!")

    task_id = management.create_task(
        "Alice task", "For Alice", ids["alice"]
    )

    auth.login("alice", "AlicePassword123!")

    management.update_status(task_id, "in_progress")

    with session_factory() as session:
        task = session.get(Task, task_id)
        assert task.status == "in_progress"


def test_user_cannot_update_another_users_task(environment):
    auth, management, _, ids = environment

    auth.login("admin", "AdminPassword123!")

    task_id = management.create_task(
        "Bob task", "For Bob", ids["bob"]
    )

    auth.login("alice", "AlicePassword123!")

    with pytest.raises(TaskManagementError):
        management.update_status(task_id, "completed")


def test_invalid_task_status_is_rejected(environment):
    auth, management, _, ids = environment

    auth.login("admin", "AdminPassword123!")

    task_id = management.create_task(
        "Alice task", "For Alice", ids["alice"]
    )

    auth.login("alice", "AlicePassword123!")

    with pytest.raises(TaskManagementError):
        management.update_status(task_id, "invalid_status")


def test_admin_can_monitor_task_statuses(environment):
    auth, management, _, ids = environment

    auth.login("admin", "AdminPassword123!")

    first_id = management.create_task(
        "Task one", "First", ids["alice"]
    )
    management.create_task(
        "Task two", "Second", ids["bob"]
    )

    auth.login("alice", "AlicePassword123!")
    management.update_status(first_id, "completed")

    auth.login("admin", "AdminPassword123!")

    summary = management.get_status_summary()

    assert summary == {
        "to_do": 1,
        "in_progress": 0,
        "completed": 1,
    }


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