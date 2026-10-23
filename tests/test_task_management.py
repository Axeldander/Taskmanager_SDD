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

def test_admin_can_edit_task(environment):
    auth, management, session_factory, ids = environment

    auth.login("admin", "AdminPassword123!")

    task_id = management.create_task(
        "Original title", "Original description", ids["alice"]
    )

    management.edit_task(
        task_id,
        title="Updated title",
        description="Updated description",
    )

    with session_factory() as session:
        task = session.get(Task, task_id)
        assert task.title == "Updated title"
        assert task.description == "Updated description"


def test_admin_can_reassign_task(environment):
    auth, management, session_factory, ids = environment

    auth.login("admin", "AdminPassword123!")

    task_id = management.create_task(
        "Reassignment task", "Description", ids["alice"]
    )

    management.reassign_task(task_id, ids["bob"])

    with session_factory() as session:
        task = session.get(Task, task_id)
        assert task.assigned_user_id == ids["bob"]


def test_admin_can_delete_task(environment):
    auth, management, session_factory, ids = environment

    auth.login("admin", "AdminPassword123!")

    task_id = management.create_task(
        "Delete me", "Description", ids["alice"]
    )

    management.delete_task(task_id)

    with session_factory() as session:
        assert session.get(Task, task_id) is None


def test_standard_user_cannot_edit_task(environment):
    auth, management, session_factory, ids = environment

    auth.login("admin", "AdminPassword123!")
    task_id = management.create_task(
        "Protected task", "Description", ids["alice"]
    )

    auth.login("alice", "AlicePassword123!")

    with pytest.raises(TaskManagementError):
        management.edit_task(task_id, title="Unauthorized edit")

    with session_factory() as session:
        assert session.get(Task, task_id).title == "Protected task"


def test_standard_user_cannot_reassign_task(environment):
    auth, management, session_factory, ids = environment

    auth.login("admin", "AdminPassword123!")
    task_id = management.create_task(
        "Protected task", "Description", ids["alice"]
    )

    auth.login("alice", "AlicePassword123!")

    with pytest.raises(TaskManagementError):
        management.reassign_task(task_id, ids["bob"])

    with session_factory() as session:
        assert session.get(Task, task_id).assigned_user_id == ids["alice"]


def test_standard_user_cannot_delete_task(environment):
    auth, management, session_factory, ids = environment

    auth.login("admin", "AdminPassword123!")
    task_id = management.create_task(
        "Protected task", "Description", ids["alice"]
    )

    auth.login("alice", "AlicePassword123!")

    with pytest.raises(TaskManagementError):
        management.delete_task(task_id)

    with session_factory() as session:
        assert session.get(Task, task_id) is not None


def test_cannot_reassign_task_to_admin(environment):
    auth, management, session_factory, ids = environment

    auth.login("admin", "AdminPassword123!")
    task_id = management.create_task(
        "Assignment task", "Description", ids["alice"]
    )

    with pytest.raises(TaskManagementError):
        management.reassign_task(task_id, ids["admin"])

    with session_factory() as session:
        assert session.get(Task, task_id).assigned_user_id == ids["alice"]


def test_cannot_edit_nonexistent_task(environment):
    auth, management, _, _ = environment

    auth.login("admin", "AdminPassword123!")

    with pytest.raises(TaskManagementError):
        management.edit_task(999999, title="Missing task")

def test_update_task_details_is_atomic(tmp_path):
    from sqlalchemy import select

    from app.database.connection import (
        create_database_engine,
        create_session_factory,
        initialize_database,
    )
    from app.models.task import Task
    from app.services.auth import AuthenticationService
    from app.services.setup import SetupService
    from app.services.user_management import UserManagementService
    from app.services.task_management import (
        TaskManagementService,
        TaskManagementError,
    )

    engine = create_database_engine(
        f"sqlite:///{(tmp_path / 'atomic_edit.db').as_posix()}"
    )
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    auth = AuthenticationService(session_factory)
    setup = SetupService(session_factory)
    setup.create_initial_admin("admin", "AdminPassword123!")
    auth.login("admin", "AdminPassword123!")

    users = UserManagementService(session_factory, auth)
    alice_id = users.create_user("alice", "AlicePassword123!")
    bob_id = users.create_user("bob", "BobPassword123!")

    tasks = TaskManagementService(session_factory, auth)

    task_id = tasks.create_task(
        "Original title", "Original description", alice_id
    )

    tasks.update_task_details(
        task_id,
        title="Updated title",
        description="Updated description",
        assigned_user_id=bob_id,
    )

    with session_factory() as session:
        task = session.get(Task, task_id)
        assert task.title == "Updated title"
        assert task.description == "Updated description"
        assert task.assigned_user_id == bob_id

    try:
        tasks.update_task_details(
            task_id,
            title="Should not be saved",
            description="Should not be saved",
            assigned_user_id=999999,
        )
    except TaskManagementError:
        pass
    else:
        raise AssertionError("Invalid reassignment should fail")

    with session_factory() as session:
        task = session.get(Task, task_id)
        assert task.title == "Updated title"
        assert task.description == "Updated description"
        assert task.assigned_user_id == bob_id

    engine.dispose()


@pytest.mark.parametrize("description", ["", "   ", "\n\t"])
def test_create_task_rejects_blank_description(environment, description):
    auth, management, session_factory, ids = environment
    auth.login("admin", "AdminPassword123!")

    with pytest.raises(TaskManagementError, match="description cannot be empty"):
        management.create_task("Invalid task", description, ids["alice"])

    with session_factory() as session:
        assert session.scalar(select(Task).where(Task.title == "Invalid task")) is None


def test_edit_task_rejects_blank_description_without_saving(environment):
    auth, management, session_factory, ids = environment
    auth.login("admin", "AdminPassword123!")
    task_id = management.create_task("Original title", "Original description", ids["alice"])

    with pytest.raises(TaskManagementError, match="description cannot be empty"):
        management.edit_task(task_id, title="Changed title", description="   ")

    with session_factory() as session:
        task = session.get(Task, task_id)
        assert task.title == "Original title"
        assert task.description == "Original description"


def test_update_task_details_rejects_blank_description_atomically(environment):
    auth, management, session_factory, ids = environment
    auth.login("admin", "AdminPassword123!")
    task_id = management.create_task("Original title", "Original description", ids["alice"])

    with pytest.raises(TaskManagementError, match="description cannot be empty"):
        management.update_task_details(
            task_id,
            title="Changed title",
            description="   ",
            assigned_user_id=ids["bob"],
        )

    with session_factory() as session:
        task = session.get(Task, task_id)
        assert task.title == "Original title"
        assert task.description == "Original description"
        assert task.assigned_user_id == ids["alice"]
