
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    username: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    tasks = relationship(
        "Task",
        back_populates="assigned_user"
    )
