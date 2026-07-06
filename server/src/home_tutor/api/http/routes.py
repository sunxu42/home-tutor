"""HTTP REST API routes."""

from fastapi import APIRouter

from home_tutor.api.http.copilot_routes import router as copilot_router
from home_tutor.api.http.session_routes import router as session_router
from home_tutor.api.http.speech_routes import router as speech_router
from home_tutor.models.session import Subject

router = APIRouter(tags=["http"])
router.include_router(copilot_router)
router.include_router(session_router)
router.include_router(speech_router)


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/subjects")
async def get_subjects() -> list[str]:
    """Return all supported subjects."""
    return [s.value for s in Subject]
