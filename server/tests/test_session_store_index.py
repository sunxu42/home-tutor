"""Tests for SessionStore session_id index cache."""

from pathlib import Path

import pytest

from home_tutor.core.config import settings
from home_tutor.services.analysis.session_store import SessionNotFoundError, SessionStore


@pytest.fixture
def store() -> SessionStore:
    return SessionStore(settings.session_fixtures_root)


def test_resolve_session_dir_uses_index(store: SessionStore) -> None:
    session_id = "a1000001-0001-4001-8001-000000000001"
    first = store.resolve_session_dir(session_id)
    second = store.resolve_session_dir(session_id)
    assert first == second
    assert store._session_dir_index is not None
    assert session_id in store._session_dir_index


def test_resolve_session_dir_missing_raises(store: SessionStore) -> None:
    with pytest.raises(SessionNotFoundError):
        store.resolve_session_dir("nonexistent-session-id")


def test_invalidate_rebuilds_index(store: SessionStore) -> None:
    session_id = "a1000001-0001-4001-8001-000000000001"
    store.resolve_session_dir(session_id)
    store.invalidate_session_dir_index()
    assert store._session_dir_index is None
    path = store.resolve_session_dir(session_id)
    assert isinstance(path, Path)
