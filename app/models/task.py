
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class Task(Base):
    __tablename__ = "tasks"

    __table_args__ = (
        CheckConstraint(
            "status IN ('to_do', 'in_progress', 'completed')",
            name="valid_task_status",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    title: Mapped[str] = mapped_column(
        String(200), nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="to_do",
        nullable=False
    )

    assigned_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    assigned_user = relationship(
        "User",
        back_populates="tasks"
    )
