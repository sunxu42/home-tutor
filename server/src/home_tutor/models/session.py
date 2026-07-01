"""Session database model."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, Float, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


class Subject(str, Enum):
    """Supported subjects."""

    CHINESE = "语文"
    MATH = "数学"
    ENGLISH = "英语"
    PHYSICS = "物理"
    CHEMISTRY = "化学"
    BIOLOGY = "生物"
    POLITICS = "政治"
    HISTORY = "历史"
    GEOGRAPHY = "地理"


class Session(Base):
    """Session entity — represents one tutoring session."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    subject: Mapped[Subject] = mapped_column(SAEnum(Subject), nullable=False)
    session_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )
