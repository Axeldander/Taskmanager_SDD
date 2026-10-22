import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.database.connection import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)

from app.models import Task, User

def make_user(username="alice"):
    return User(
        username=username,
        password_hash="test-hash",
        role="user",
    )
def test_database_connection(tmp_path):
    engine = create_database_engine(
        f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    )

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar() == 1

    engine.dispose()



def test_database_initialization(tmp_path):
    database_path = tmp_path / "test.db"

    engine = create_database_engine(
        f"sqlite:///{database_path.as_posix()}"
    )

    initialize_database(engine)

    # Check that SQLite created the database file.
    assert database_path.exists()

    # Check that SQLAlchemy created both required tables.
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    assert "users" in table_names
    assert "tasks" in table_names

    engine.dispose()


def test_session_factory(tmp_path):
    engine = create_database_engine(
        f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    )

    session_factory = create_session_factory(engine)

    with session_factory() as session:
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    engine.dispose()


def test_data_persists_across_sessions(tmp_path):
    """Verify that saved records survive closing and reopening a session."""

    database_path = tmp_path / "persistence.db"
    database_url = f"sqlite:///{database_path.as_posix()}"

    engine = create_database_engine(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    # First session: save a user and an assigned task.
    with session_factory() as session:
        user = make_user("persistent_user")
        session.add(user)
        session.flush()

        task = Task(
            title="Persistent task",
            description="This task should remain saved",
            assigned_user_id=user.id,
        )

        session.add(task)
        session.commit()

    # Close the database engine to simulate a fresh connection.
    engine.dispose()

    # Second engine and session: verify records are still present.
    engine = create_database_engine(database_url)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        saved_user = session.query(User).filter_by(
            username="persistent_user"
        ).one()

        saved_task = session.query(Task).filter_by(
            title="Persistent task"
        ).one()

        assert saved_task.assigned_user_id == saved_user.id
        assert saved_task.status == "to_do"

    engine.dispose()


def test_transaction_rollback_prevents_partial_save(tmp_path):
    """Verify that a failed transaction does not partially save data."""

    database_path = tmp_path / "rollback.db"
    database_url = f"sqlite:///{database_path.as_posix()}"

    engine = create_database_engine(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        # Both users are part of the same transaction.
        session.add(make_user("duplicate_user"))

        session.add(make_user("duplicate_user"))

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()

    # Verify that neither record was saved.
    with session_factory() as session:
        saved_users = session.query(User).filter_by(
            username="duplicate_user"
        ).all()

        assert saved_users == []

    engine.dispose()
