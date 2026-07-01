"""Pydantic schemas for Session API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from home_tutor.models.session import Subject


class SessionCreate(BaseModel):
    """Schema for creating a session."""

    id: str | None = None
    subject: Subject
    session_time: datetime
    accuracy: float


class SessionUpdate(BaseModel):
    """Schema for updating a session."""

    subject: Subject | None = None
    session_time: datetime | None = None
    accuracy: float | None = None


class SessionResponse(BaseModel):
    """Schema for session response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    subject: Subject
    session_time: datetime
    accuracy: float
    created_at: datetime
    updated_at: datetime


class DeleteResponse(BaseModel):
    """Schema for delete confirmation."""

    ok: bool
