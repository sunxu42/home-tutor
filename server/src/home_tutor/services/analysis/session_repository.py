"""Unified session access: SQLite index + filesystem content."""

from __future__ import annotations

import asyncio
from pathlib import Path

from home_tutor.models.review import QuestionDetailResponse, TutorViewBase
from home_tutor.models.schemas import SessionCreate, SessionUpdate
from home_tutor.models.session import Session, Subject
from home_tutor.models.database import get_db_session
from home_tutor.services.analysis.session_crud import (
    create_session,
    delete_session,
    get_session,
    get_sessions,
    update_session,
)
from home_tutor.services.analysis.session_store import SessionStore


class SessionRepository:
    """Facade over SQLite session index and filesystem session content."""

    def __init__(self, fixtures_root: Path) -> None:
        self._store = SessionStore(fixtures_root)

    @property
    def store(self) -> SessionStore:
        """Underlying filesystem store for services that write content."""
        return self._store

    async def list_sessions(
        self,
        *,
        subject: Subject | None,
        session_ids: list[str],
    ) -> list[Session]:
        async with get_db_session() as db:
            return await get_sessions(db, subject=subject, session_ids=session_ids)

    async def get_session(self, session_id: str) -> Session | None:
        async with get_db_session() as db:
            return await get_session(db, session_id)

    async def create_session(self, data: SessionCreate) -> Session:
        async with get_db_session() as db:
            return await create_session(
                db,
                subject=data.subject,
                session_time=data.session_time,
                accuracy=data.accuracy,
                session_id=data.id,
            )

    async def update_session(self, session_id: str, data: SessionUpdate) -> Session | None:
        async with get_db_session() as db:
            return await update_session(
                db,
                session_id,
                subject=data.subject,
                session_time=data.session_time,
                accuracy=data.accuracy,
            )

    async def delete_session(self, session_id: str) -> bool:
        async with get_db_session() as db:
            return await delete_session(db, session_id)

    async def get_tutor_view(self, session_id: str) -> TutorViewBase:
        raw = await asyncio.to_thread(self._store.build_tutor_view, session_id)
        return TutorViewBase.model_validate(raw)

    async def get_question_detail(self, session_id: str, question_id: str) -> QuestionDetailResponse:
        raw = await asyncio.to_thread(self._store.build_question_detail, session_id, question_id)
        return QuestionDetailResponse.model_validate(raw)

    async def read_tutor(self, session_id: str, question_id: str) -> dict:
        return await asyncio.to_thread(self._store.read_tutor, session_id, question_id)

    async def read_meta(self, session_id: str) -> dict:
        return await asyncio.to_thread(self._store.read_meta, session_id)

    async def read_package(self, session_id: str, question_id: str) -> dict:
        return await asyncio.to_thread(self._store.read_package, session_id, question_id)

    def normalize_tutor_dict(self, tutor: dict) -> dict:
        """Back-compat for fixture files written before analysis_status existed."""
        if "analysis_status" not in tutor:
            return {**tutor, "analysis_status": "ready"}
        return tutor

    async def get_question_detail_for_view(
        self,
        session_id: str,
        question_id: str,
    ) -> QuestionDetailResponse:
        """Load question detail with tutor field refreshed after optional analysis scheduling."""
        detail = await self.get_question_detail(session_id, question_id)
        tutor_dict = self.normalize_tutor_dict(detail.tutor.model_dump())
        return detail.model_copy(
            update={"tutor": detail.tutor.model_validate(tutor_dict)},
        )

    async def refresh_tutor_in_detail(
        self,
        session_id: str,
        question_id: str,
        detail: QuestionDetailResponse,
    ) -> QuestionDetailResponse:
        """Re-read tutor content only (avoids full detail rebuild)."""
        tutor_dict = self.normalize_tutor_dict(
            await self.read_tutor(session_id, question_id),
        )
        return detail.model_copy(
            update={"tutor": detail.tutor.model_validate(tutor_dict)},
        )
