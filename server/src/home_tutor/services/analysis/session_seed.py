"""Seed SQLite session rows from filesystem fixture meta.json files."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from home_tutor.models.session import Subject
from home_tutor.services.analysis.session_crud import (
    create_session,
    get_session,
    update_session,
)

_SUBJECT_CODE_TO_ENUM: dict[str, Subject] = {
    "chinese": Subject.CHINESE,
    "math": Subject.MATH,
    "english": Subject.ENGLISH,
    "physics": Subject.PHYSICS,
    "chemistry": Subject.CHEMISTRY,
    "biology": Subject.BIOLOGY,
    "politics": Subject.POLITICS,
    "history": Subject.HISTORY,
    "geography": Subject.GEOGRAPHY,
}

_SCORE_DIR_PATTERN = re.compile(r"^score(\d+)$", re.IGNORECASE)


def _accuracy_from_dir_name(dir_name: str) -> float | None:
    match = _SCORE_DIR_PATTERN.match(dir_name)
    if match is None:
        return None
    return float(match.group(1))


def _parse_subject(subject_code: str) -> Subject:
    return _SUBJECT_CODE_TO_ENUM.get(subject_code.lower(), Subject.MATH)


def _parse_session_time(started_at: str) -> datetime:
    session_time = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    if session_time.tzinfo is not None:
        return session_time.replace(tzinfo=None)
    return session_time


def _load_fixture_meta(child: Path) -> dict | None:
    """Return parsed meta.json when the directory is a valid fixture session."""
    meta_path = child / "meta.json"
    if not child.is_dir() or not meta_path.is_file():
        return None

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    session_id = meta.get("session_id")
    started_at = meta.get("started_at")
    if not session_id or not started_at:
        return None

    accuracy = meta.get("accuracy_percent")
    if accuracy is None:
        parsed = _accuracy_from_dir_name(child.name)
        if parsed is None:
            return None
        accuracy = parsed

    return {
        "session_id": session_id,
        "started_at": started_at,
        "accuracy": float(accuracy),
        "subject": _parse_subject(meta.get("subject", "math")),
    }


async def seed_sessions_from_fixtures(db: AsyncSession, fixtures_root: Path) -> int:
    """Insert DB rows for fixture sessions that are not yet in the database."""
    summary = await sync_sessions_from_fixtures(db, fixtures_root)
    return summary["created"]


async def sync_sessions_from_fixtures(db: AsyncSession, fixtures_root: Path) -> dict[str, int]:
    """Upsert SQLite rows from fixture meta and remove stale fixture-only rows."""
    if not fixtures_root.is_dir():
        return {"created": 0, "updated": 0, "deleted": 0}

    fixture_rows: list[dict] = []
    for child in sorted(fixtures_root.iterdir()):
        row = _load_fixture_meta(child)
        if row is not None:
            fixture_rows.append(row)

    created = 0
    updated = 0

    for row in fixture_rows:
        session_id = row["session_id"]
        session_time = _parse_session_time(row["started_at"])
        existing = await get_session(db, session_id)
        if existing is None:
            await create_session(
                db,
                subject=row["subject"],
                session_time=session_time,
                accuracy=row["accuracy"],
                session_id=session_id,
            )
            created += 1
            continue

        needs_update = (
            existing.subject != row["subject"]
            or existing.session_time != session_time
            or existing.accuracy != row["accuracy"]
        )
        if needs_update:
            await update_session(
                db,
                session_id,
                subject=row["subject"],
                session_time=session_time,
                accuracy=row["accuracy"],
            )
            updated += 1

    return {"created": created, "updated": updated, "deleted": 0}
