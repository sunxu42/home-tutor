"""Session CRUD operations."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from home_tutor.models.session import Session, Subject


async def create_session(
    db: AsyncSession,
    subject: Subject,
    session_time: datetime,
    accuracy: float,
    session_id: str | None = None,
) -> Session:
    """Create a new session."""
    session = Session(
        id=session_id,
        subject=subject,
        session_time=session_time,
        accuracy=accuracy,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: str) -> Session | None:
    """Get a session by ID."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    return result.scalar_one_or_none()


async def get_sessions(
    db: AsyncSession,
    subject: Subject | None = None,
) -> list[Session]:
    """Get all sessions, optionally filtered by subject. Ordered by session_time desc."""
    stmt = select(Session)
    if subject is not None:
        stmt = stmt.where(Session.subject == subject)
    stmt = stmt.order_by(Session.session_time.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_session(
    db: AsyncSession,
    session_id: str,
    subject: Subject | None = None,
    session_time: datetime | None = None,
    accuracy: float | None = None,
) -> Session | None:
    """Update a session. Returns None if not found."""
    session = await get_session(db, session_id)
    if session is None:
        return None
    if subject is not None:
        session.subject = subject
    if session_time is not None:
        session.session_time = session_time
    if accuracy is not None:
        session.accuracy = accuracy
    await db.flush()
    await db.refresh(session)
    return session


async def delete_session(db: AsyncSession, session_id: str) -> bool:
    """Delete a session. Returns True if deleted, False if not found."""
    session = await get_session(db, session_id)
    if session is None:
        return False
    await db.delete(session)
    return True
