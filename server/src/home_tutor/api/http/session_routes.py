"""Session CRUD and review HTTP routes."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from home_tutor.api.deps import get_analysis_service, get_session_repository
from home_tutor.core.config import settings
from home_tutor.models import DeleteResponse, SessionCreate, SessionResponse, SessionUpdate
from home_tutor.models.review import (
    AnalyzeQuestionResponse,
    QuestionDetailResponse,
    TutorAnalysisPolicyResponse,
    TutorViewResponse,
)
from home_tutor.models.session import Subject
from home_tutor.services.analysis.session_repository import SessionRepository
from home_tutor.services.analysis.session_seed import list_fixture_session_ids
from home_tutor.services.analysis.session_store import SessionNotFoundError
from home_tutor.services.llm.analysis_service import TutorAnalysisService, format_sse

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    subject: Subject | None = Query(None),
    repo: SessionRepository = Depends(get_session_repository),
) -> list[SessionResponse]:
    """List fixture-backed sessions for the bookshelf. Ordered by session_time desc."""
    reviewable_ids = list_fixture_session_ids(settings.session_fixtures_root)
    sessions = await repo.list_sessions(subject=subject, session_ids=reviewable_ids)
    return [SessionResponse.model_validate(s) for s in sessions]


@router.post("", response_model=SessionResponse)
async def create_session_endpoint(
    data: SessionCreate,
    repo: SessionRepository = Depends(get_session_repository),
) -> SessionResponse:
    """Create a new session."""
    session = await repo.create_session(data)
    return SessionResponse.model_validate(session)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_endpoint(
    session_id: str,
    repo: SessionRepository = Depends(get_session_repository),
) -> SessionResponse:
    """Get a session by ID."""
    session = await repo.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse.model_validate(session)


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session_endpoint(
    session_id: str,
    data: SessionUpdate,
    repo: SessionRepository = Depends(get_session_repository),
) -> SessionResponse:
    """Update a session."""
    session = await repo.update_session(session_id, data)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse.model_validate(session)


@router.delete("/{session_id}", response_model=DeleteResponse)
async def delete_session_endpoint(
    session_id: str,
    repo: SessionRepository = Depends(get_session_repository),
) -> DeleteResponse:
    """Delete a session."""
    deleted = await repo.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return DeleteResponse(ok=True)


@router.get("/{session_id}/tutor-view", response_model=TutorViewResponse)
async def get_tutor_view(
    session_id: str,
    repo: SessionRepository = Depends(get_session_repository),
    analysis: TutorAnalysisService = Depends(get_analysis_service),
) -> TutorViewResponse:
    """Return timeline index and per-question summaries for the review page."""
    try:
        view = await repo.get_tutor_view(session_id)
        meta = await repo.read_meta(session_id)
        policy = analysis.build_analysis_policy(meta)
        return TutorViewResponse(
            timeline_index=view.timeline_index,
            questions=view.questions,
            analysis_policy=TutorAnalysisPolicyResponse.model_validate(policy.to_api_dict()),
        )
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{session_id}/questions/{question_id}", response_model=QuestionDetailResponse)
async def get_question_detail(
    session_id: str,
    question_id: str,
    repo: SessionRepository = Depends(get_session_repository),
    analysis: TutorAnalysisService = Depends(get_analysis_service),
) -> QuestionDetailResponse:
    """Return materialized package and tutor content for one question."""
    try:
        detail = await repo.get_question_detail_for_view(session_id, question_id)
        await analysis.schedule_on_view_if_needed(
            session_id,
            question_id,
            detail.tutor.model_dump(),
        )
        return await repo.refresh_tutor_in_detail(session_id, question_id, detail)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{session_id}/questions/{question_id}/analyze", response_model=AnalyzeQuestionResponse)
async def analyze_question(
    session_id: str,
    question_id: str,
    repo: SessionRepository = Depends(get_session_repository),
    analysis: TutorAnalysisService = Depends(get_analysis_service),
) -> AnalyzeQuestionResponse:
    """Trigger LLM tutor analysis for one question."""
    try:
        await repo.read_package(session_id, question_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not analysis.llm_settings.is_configured():
        raise HTTPException(status_code=503, detail="LLM provider not configured")

    status = await analysis.schedule(session_id, question_id, reason="manual_analyze", force=True)
    return AnalyzeQuestionResponse(analysis_status=status)


@router.get("/{session_id}/questions/{question_id}/tutor/events")
async def tutor_events(
    session_id: str,
    question_id: str,
    repo: SessionRepository = Depends(get_session_repository),
    analysis: TutorAnalysisService = Depends(get_analysis_service),
) -> StreamingResponse:
    """SSE stream for tutor analysis status and final content."""
    try:
        await repo.read_package(session_id, question_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    async def event_stream():
        async for event in analysis.subscribe(session_id, question_id):
            yield format_sse(event)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
