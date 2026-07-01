"""Session CRUD and review HTTP routes."""

import asyncio

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from home_tutor.core.config import settings
from home_tutor.models import DeleteResponse, SessionCreate, SessionResponse, SessionUpdate
from home_tutor.models.session import Subject
from home_tutor.models.database import get_db_session
from home_tutor.services.analysis.session_crud import (
    create_session,
    delete_session,
    get_session,
    get_sessions,
    update_session,
)
from home_tutor.services.analysis.session_store import SessionNotFoundError, SessionStore
from home_tutor.services.llm.analysis_service import format_sse, get_analysis_service

router = APIRouter(prefix="/sessions", tags=["sessions"])

_store = SessionStore(settings.session_fixtures_root)
_analysis = get_analysis_service()


def _normalize_tutor(tutor: dict) -> dict:
    """Back-compat for fixture files written before analysis_status existed."""
    if "analysis_status" not in tutor:
        tutor = {**tutor, "analysis_status": "ready"}
    return tutor


@router.get("", response_model=list[SessionResponse])
async def list_sessions(subject: Subject | None = Query(None)) -> list[SessionResponse]:
    """List all sessions, optionally filtered by subject. Ordered by session_time desc."""
    async with get_db_session() as db:
        sessions = await get_sessions(db, subject=subject)
        return [SessionResponse.model_validate(s) for s in sessions]


@router.post("", response_model=SessionResponse)
async def create_session_endpoint(data: SessionCreate) -> SessionResponse:
    """Create a new session."""
    async with get_db_session() as db:
        session = await create_session(
            db,
            subject=data.subject,
            session_time=data.session_time,
            accuracy=data.accuracy,
            session_id=data.id,
        )
        return SessionResponse.model_validate(session)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_endpoint(session_id: str) -> SessionResponse:
    """Get a session by ID."""
    async with get_db_session() as db:
        session = await get_session(db, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return SessionResponse.model_validate(session)


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session_endpoint(session_id: str, data: SessionUpdate) -> SessionResponse:
    """Update a session."""
    async with get_db_session() as db:
        session = await update_session(
            db,
            session_id,
            subject=data.subject,
            session_time=data.session_time,
            accuracy=data.accuracy,
        )
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return SessionResponse.model_validate(session)


@router.delete("/{session_id}", response_model=DeleteResponse)
async def delete_session_endpoint(session_id: str) -> DeleteResponse:
    """Delete a session."""
    async with get_db_session() as db:
        deleted = await delete_session(db, session_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Session not found")
        return DeleteResponse(ok=True)


@router.get("/{session_id}/tutor-view")
async def get_tutor_view(session_id: str) -> dict:
    """Return timeline index and per-question summaries for the review page."""
    try:
        view = await asyncio.to_thread(_store.build_tutor_view, session_id)
        meta = await asyncio.to_thread(_store.read_meta, session_id)
        view["analysis_policy"] = _analysis.build_analysis_policy(meta).to_api_dict()
        return view
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{session_id}/questions/{question_id}")
async def get_question_detail(session_id: str, question_id: str) -> dict:
    """Return materialized package and tutor content for one question."""
    try:
        detail = await asyncio.to_thread(_store.build_question_detail, session_id, question_id)
        detail["tutor"] = _normalize_tutor(detail["tutor"])
        await _analysis.schedule_on_view_if_needed(session_id, question_id, detail["tutor"])
        detail = await asyncio.to_thread(_store.build_question_detail, session_id, question_id)
        detail["tutor"] = _normalize_tutor(detail["tutor"])
        return detail
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{session_id}/questions/{question_id}/analyze")
async def analyze_question(session_id: str, question_id: str) -> dict:
    """Trigger LLM tutor analysis for one question."""
    try:
        await asyncio.to_thread(_store.read_package, session_id, question_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not _analysis.llm_settings.is_configured():
        raise HTTPException(status_code=503, detail="LLM provider not configured")

    status = await _analysis.schedule(session_id, question_id, reason="manual_analyze", force=True)
    return {"analysis_status": status}


@router.get("/{session_id}/questions/{question_id}/tutor/events")
async def tutor_events(session_id: str, question_id: str) -> StreamingResponse:
    """SSE stream for tutor analysis status and final content."""
    try:
        await asyncio.to_thread(_store.read_package, session_id, question_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    async def event_stream():
        async for event in _analysis.subscribe(session_id, question_id):
            yield format_sse(event)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
