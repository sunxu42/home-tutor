"""Sync SQLite session index rows from filesystem fixture meta.json files."""

from __future__ import annotations

import asyncio
import sys

from home_tutor.core.config import settings
from home_tutor.models.database import _async_session_factory
from home_tutor.services.analysis.session_seed import sync_sessions_from_fixtures


async def _main() -> int:
    async with _async_session_factory() as db:
        summary = await sync_sessions_from_fixtures(db, settings.session_fixtures_root)
        await db.commit()
    print(
        "Fixture sync complete: "
        f"created={summary['created']} "
        f"updated={summary['updated']} "
        f"deleted={summary['deleted']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
