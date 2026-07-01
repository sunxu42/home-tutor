"""Factory helpers for analysis pipeline wiring."""

from __future__ import annotations

from home_tutor.services.analysis.package_updater import PackageUpdater
from home_tutor.services.analysis.session_store import SessionStore
from home_tutor.services.llm.analysis_service import get_analysis_service


def create_package_updater(store: SessionStore) -> PackageUpdater:
    """Build a PackageUpdater that notifies the tutor analysis service."""
    analysis = get_analysis_service()

    def _on_updated(session_id: str, question_id: str, answer_changed: bool) -> None:
        analysis.on_package_updated(session_id, question_id, answer_changed=answer_changed)

    return PackageUpdater(store, on_package_updated=_on_updated)
