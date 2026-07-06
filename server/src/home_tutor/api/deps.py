"""FastAPI dependency injection for shared services."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from home_tutor.core.config import settings
from home_tutor.services.analysis.session_repository import SessionRepository
from home_tutor.services.analysis.session_store import SessionStore
from home_tutor.services.llm.analysis_service import TutorAnalysisService


@lru_cache
def _session_store() -> SessionStore:
    return SessionStore(settings.session_fixtures_root)


@lru_cache
def _session_repository() -> SessionRepository:
    return SessionRepository(settings.session_fixtures_root)


_analysis_service: TutorAnalysisService | None = None


def get_session_store() -> SessionStore:
    """Return the filesystem session store singleton."""
    return _session_store()


def get_session_repository() -> SessionRepository:
    """Return the unified session repository singleton."""
    return _session_repository()


def get_analysis_service(
    store: SessionStore = Depends(get_session_store),
) -> TutorAnalysisService:
    """Return the tutor analysis service, sharing the injected store."""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = TutorAnalysisService(store=store)
    elif _analysis_service.store is not store:
        _analysis_service.store = store
    return _analysis_service


def reset_analysis_service_for_tests() -> None:
    """Clear cached analysis service (test helper)."""
    global _analysis_service
    _analysis_service = None
    _session_store.cache_clear()
    _session_repository.cache_clear()
