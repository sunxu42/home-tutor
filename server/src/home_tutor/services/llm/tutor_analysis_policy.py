"""Configurable LLM tutor analysis strategy for mock vs live sessions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DataSource(str, Enum):
    """Whether review data comes from fixtures or a real captured session."""

    MOCK = "mock"
    LIVE = "live"


def resolve_data_source(meta: dict[str, Any]) -> DataSource:
    """Infer session data source from session meta.json."""
    metadata = meta.get("metadata") or {}
    if metadata.get("mock") is True:
        return DataSource.MOCK

    explicit = metadata.get("data_source") or meta.get("data_source")
    if explicit == DataSource.MOCK.value:
        return DataSource.MOCK
    if explicit == DataSource.LIVE.value:
        return DataSource.LIVE

    # Fixture sessions generated for local demo include student_profile metadata.
    if metadata.get("student_profile"):
        return DataSource.MOCK

    return DataSource.LIVE


@dataclass(frozen=True)
class TutorAnalysisPolicy:
    """Resolved analysis behavior for one session."""

    data_source: DataSource
    save_token_mode: bool

    @classmethod
    def for_session(cls, meta: dict[str, Any], *, save_token_mode: bool) -> TutorAnalysisPolicy:
        """Build policy from session meta and global LLM settings."""
        return cls(
            data_source=resolve_data_source(meta),
            save_token_mode=save_token_mode,
        )

    @property
    def is_mock(self) -> bool:
        return self.data_source == DataSource.MOCK

    def to_api_dict(self) -> dict[str, bool | str]:
        """Serialize for tutor-view API consumers."""
        prefetch = self.should_prefetch_on_select()
        return {
            "data_source": self.data_source.value,
            "manual_only": self.is_mock or self.save_token_mode,
            "prefetch_on_select": prefetch,
            "auto_analyze_on_view": self.should_auto_analyze_on_view(
                {"analysis_status": "missing", "stale": False},
            ),
        }

    def should_auto_analyze_on_view(self, tutor: dict[str, Any]) -> bool:
        """Whether opening a question should trigger LLM without user action."""
        if self.is_mock:
            return False

        status = tutor.get("analysis_status", "ready")
        if status in {"ready", "generating", "pending"} and not tutor.get("stale"):
            return False
        if self.save_token_mode and status == "missing":
            return False
        return True

    def should_prefetch_on_select(self) -> bool:
        """Whether timeline selection may prefetch LLM for wrong answers."""
        if self.is_mock:
            return False
        return not self.save_token_mode

    def should_auto_analyze_on_package_update(self, *, answer_changed: bool) -> bool:
        """Whether package materialization should enqueue LLM analysis."""
        if self.is_mock:
            return False
        if self.save_token_mode:
            return False
        return True

    def should_write_missing_on_schedule(self, *, force: bool) -> bool:
        """Whether a non-forced schedule should persist a missing tutor shell."""
        if force or self.is_mock:
            return False
        return self.save_token_mode

    def should_skip_schedule(self, tutor: dict[str, Any] | None, *, force: bool) -> bool:
        """Whether schedule should no-op and keep the existing tutor document."""
        if force:
            return False
        if tutor is None:
            return False
        if self.is_mock:
            status = tutor.get("analysis_status", "ready")
            return status in {"ready", "generating", "pending"} and not tutor.get("stale")
        return False
