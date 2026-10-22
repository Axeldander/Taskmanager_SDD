
import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.database.connection import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from app.models import Task, User


@pytest.fixture
def db_session(tmp_path):
    engine = create_database_engine(
        f"sqlite:///{(tmp_path / 'models.db').as_posix()}"
    )
    initialize_database(engine)

    session_factory = create_session_factory(engine)

    with session_factory() as session:
        yield session

    engine.dispose()


def make_user(username="alice"):
    return User(
        username=username,
        password_hash="test-hash-not-a-real-password",
        role="user",
    )


def test_database_tables_exist(db_session):
    inspector = inspect(db_session.bind)

    assert "users" in inspector.get_table_names()
    assert "tasks" in inspector.get_table_names()


def test_create_user(db_session):
    user = make_user()

    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.username == "alice"


def test_duplicate_username_rejected(db_session):
    db_session.add(make_user("alice"))
    db_session.commit()

    db_session.add(make_user("alice"))

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_create_assigned_task(db_session):
    user = make_user()
    db_session.add(user)
    db_session.commit()

    task = Task(
        title="Write project report",
        description="Complete the SDD documentation",
        assigned_user_id=user.id,
    )

    db_session.add(task)
    db_session.commit()

    assert task.id is not None
    assert task.status == "to_do"
    assert task.assigned_user_id == user.id


def test_task_requires_assigned_user(db_session):
    task = Task(
        title="Unassigned task",
        description="This should fail",
    )

    db_session.add(task)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_invalid_task_status_rejected(db_session):
    user = make_user()
    db_session.add(user)
    db_session.commit()

    task = Task(
        title="Invalid task",
        description="Testing status validation",
        status="invalid",
        assigned_user_id=user.id,
    )

    db_session.add(task)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()
