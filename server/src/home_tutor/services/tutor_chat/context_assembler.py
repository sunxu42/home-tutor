"""Assemble and trim tutor session context for chat rounds."""

from __future__ import annotations

from typing import Any

from home_tutor.models.tutor_session_context import TutorSessionContext


def trim_transcript(
    entries: list[dict[str, Any]],
    *,
    max_entries: int = 10,
) -> list[dict[str, Any]]:
    """Keep only the most recent transcript entries."""
    if len(entries) <= max_entries:
        return entries
    return entries[-max_entries:]


def build_process_summary(package: dict[str, Any]) -> str:
    """Summarize writing process metrics for the LLM."""
    metrics = package.get("process_metrics") or {}
    revisions = metrics.get("revision_count", 0)
    active_ms = metrics.get("active_duration_ms", 0)
    return f"用时约{active_ms // 1000}秒，修改{revisions}次"


def assemble_context(raw: dict[str, Any]) -> TutorSessionContext:
    """Validate client metadata and enrich server-side fields."""
    data = dict(raw)
    data["transcript"] = trim_transcript(data.get("transcript") or [])
    package = dict(data.get("package") or {})
    if not package.get("process_summary"):
        package["process_summary"] = build_process_summary(package)
        data["package"] = package
    return TutorSessionContext.model_validate(data)
