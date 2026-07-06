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
async def test_sync_deletes_orphan_db_rows(tmp_path: Path) -> None:
    fixture_session_id = "e4000001-0001-4001-8001-000000001"
    orphan_session_id = "deadbeef-dead-beef-dead-beefdeadbeef"
    fixtures_root = tmp_path / "sessions"
    fixture_dir = fixtures_root / "score53"
    fixture_dir.mkdir(parents=True)
    (fixture_dir / "meta.json").write_text(
        json.dumps(
            {
                "session_id": fixture_session_id,
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
            session_id=fixture_session_id,
        )
        await create_session(
            db,
            subject=Subject.MATH,
            session_time=__import__("datetime").datetime(2026, 6, 21, 14, 0, 0),
            accuracy=12.0,
            session_id=orphan_session_id,
        )
        await db.commit()

    async with _async_session_factory() as db:
        summary = await sync_sessions_from_fixtures(db, fixtures_root)
        await db.commit()
        assert summary["created"] == 0
        assert summary["updated"] == 1
        assert summary["deleted"] >= 1

        fixture_row = (
            await db.execute(select(Session).where(Session.id == fixture_session_id))
        ).scalar_one_or_none()
        orphan_row = (
            await db.execute(select(Session).where(Session.id == orphan_session_id))
        ).scalar_one_or_none()
        assert fixture_row is not None
        assert fixture_row.accuracy == 73.0
        assert orphan_row is None


@pytest.mark.asyncio
async def test_sync_updates_existing_session_rows(tmp_path: Path) -> None:
    session_id = "e4000002-0002-4002-8002-000000002"
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
        assert summary["created"] == 0
        assert summary["updated"] == 1

        row = (
            await db.execute(select(Session).where(Session.id == session_id))
        ).scalar_one()
        assert row.accuracy == 73.0
        assert row.session_time.isoformat(sep=" ") == "2026-06-20 15:30:00"
