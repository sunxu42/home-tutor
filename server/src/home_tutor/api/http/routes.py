"""HTTP REST API routes."""

from fastapi import APIRouter

from home_tutor.api.http.session_routes import router as session_router
from home_tutor.models.session import Subject

router = APIRouter(tags=["http"])
router.include_router(session_router)


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/data")
async def get_data() -> dict[str, str]:
    """Placeholder — return analyzed data for the client."""
    return {"message": "Data endpoint — implement analysis service here"}


@router.get("/subjects")
async def get_subjects() -> list[str]:
    """Return all supported subjects."""
    return [s.value for s in Subject]
