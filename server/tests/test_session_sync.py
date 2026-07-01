"""Tests for fixture session sync."""

import json
from pathlib import Path

import pytest
from sqlalchemy import select

from home_tutor.models.database import _async_session_factory
from home_tutor.models.session import Session, Subject
from home_tutor.services.analysis.session_crud import create_session
from home_tutor.services.analysis.session_seed import sync_sessions_from_fixtures


@pytest.mark.asyncio
async def test_sync_updates_existing_session_rows(tmp_path: Path) -> None:
    session_id = "f0000001-0001-4001-8001-000000000099"
    fixtures_root = tmp_path / "sessions"
    fixture_dir = fixtures_root / "score53"
    fixture_dir.mkdir(parents=True)
    (fixture_dir / "meta.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "subject": "math",
                "started_at": "2026-06-20T15:30:00.000Z",
                "accuracy_percent": 73.0,
                "questions": [],
            }
        ),
        encoding="utf-8",
    )

    async with _async_session_factory() as db:
        await create_session(
            db,
            subject=Subject.MATH,
            session_time=__import__("datetime").datetime(2026, 6, 22, 14, 0, 0),
            accuracy=50.0,
            session_id=session_id,
        )
        await db.commit()

    async with _async_session_factory() as db:
        summary = await sync_sessions_from_fixtures(db, fixtures_root)
        await db.commit()
        assert summary == {"created": 0, "updated": 1, "deleted": 0}

        row = (
            await db.execute(select(Session).where(Session.id == session_id))
        ).scalar_one()
        assert row.accuracy == 73.0
        assert row.session_time.isoformat(sep=" ") == "2026-06-20 15:30:00"
