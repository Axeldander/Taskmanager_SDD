
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database.base import Base


DATA_DIR = Path.home() / ".desktop_task_manager"
DATABASE_PATH = DATA_DIR / "tasks.db"


def create_database_engine(database_url=None):
    """Create the database engine."""

    if database_url is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        database_url = f"sqlite:///{DATABASE_PATH.as_posix()}"

    engine = create_engine(database_url)

    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def create_session_factory(engine):
    """Return a factory for database sessions."""
    return sessionmaker(bind=engine, expire_on_commit=False)


def initialize_database(engine):
    """Create database tables for registered models."""
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
