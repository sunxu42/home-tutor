"""SQLAlchemy async engine and session management."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from home_tutor.core.config import settings

_db_path = Path(settings.data_dir) / "home_tutor.db"
_db_path.parent.mkdir(parents=True, exist_ok=True)

_engine = create_async_engine(
    f"sqlite+aiosqlite:///{_db_path}",
    echo=False,
)

_async_session_factory = async_sessionmaker(
    _engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Create all tables and seed fixture sessions into SQLite when missing."""
    from home_tutor.models.session import Base  # noqa: F401
    from home_tutor.services.analysis.session_seed import sync_sessions_from_fixtures

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with _async_session_factory() as session:
        try:
            await sync_sessions_from_fixtures(session, settings.session_fixtures_root)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Get an async database session."""
    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
