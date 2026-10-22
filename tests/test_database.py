
from sqlalchemy import text

from app.database.connection import (
    create_database_engine,
    create_session_factory,
    initialize_database,
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

    assert database_path.exists()

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
