"""Generate TutorContent fields from a QuestionProcessPackage via LLM."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from langfuse import observe, propagate_attributes

from home_tutor.services.llm.client import LlmClient, LlmClientError
from home_tutor.services.llm.config import LlmProviderConfig
from home_tutor.services.llm.prompts import SYSTEM_PROMPT, build_user_prompt

_VALID_VERDICTS = frozenset({"correct", "wrong", "unknown"})
_VALID_CATEGORIES = frozenset(
    {"correct", "concept_error", "calculation_error", "incomplete", "unknown"}
)


def _empty_tutor_shell(
    *,
    session_id: str,
    question_id: str,
    analysis_status: str,
) -> dict[str, Any]:
    return {
        "schema_version": "home-tutor.tutor-content.v1",
        "session_id": session_id,
        "question_id": question_id,
        "analysis_status": analysis_status,
        "verdict": "unknown",
        "reference_answer": "",
        "summary": "",
        "explanation_paragraphs": [],
        "stale": False,
        "error": None,
    }


def normalize_llm_payload(
    *,
    session_id: str,
    question_id: str,
    payload: dict[str, Any],
    model: str,
) -> dict[str, Any]:
    """Validate and normalize LLM JSON into TutorContent."""
    verdict = payload.get("verdict", "unknown")
    if verdict not in _VALID_VERDICTS:
        verdict = "unknown"

    paragraphs = payload.get("explanation_paragraphs", [])
    if not isinstance(paragraphs, list):
        paragraphs = []
    paragraphs = [str(p) for p in paragraphs if str(p).strip()]
    if not paragraphs:
        paragraphs = [payload.get("summary", "") or "已完成分析。"]

    tutor: dict[str, Any] = {
        "schema_version": "home-tutor.tutor-content.v1",
        "session_id": session_id,
        "question_id": question_id,
        "analysis_status": "ready",
        "verdict": verdict,
        "reference_answer": str(payload.get("reference_answer", "")),
        "summary": str(payload.get("summary", "")),
        "explanation_paragraphs": paragraphs,
        "actions": [
            {"id": "explain_more", "label": "详细讲讲", "enabled": True},
            {"id": "give_hint", "label": "给个提示", "enabled": True},
        ],
        "stale": False,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "model": model,
        "error": None,
    }

    if payload.get("process_comment"):
        tutor["process_comment"] = str(payload["process_comment"])

    error_cls = payload.get("error_classification")
    if isinstance(error_cls, dict):
        category = error_cls.get("category", "unknown")
        if category not in _VALID_CATEGORIES:
            category = "unknown"
        normalized: dict[str, Any] = {"category": category}
        if error_cls.get("subcategory"):
            normalized["subcategory"] = str(error_cls["subcategory"])
        if isinstance(error_cls.get("confidence"), (int, float)):
            normalized["confidence"] = float(error_cls["confidence"])
        tutor["error_classification"] = normalized

    return tutor


class TutorGenerator:
    """Call LLM to produce tutor content for one question package."""

    def __init__(self, client: LlmClient | None = None) -> None:
        self._client = client or LlmClient()

    @observe(name="tutor-generate")
    async def generate(
        self,
        provider: LlmProviderConfig,
        *,
        session_id: str,
        question_id: str,
        package: dict[str, Any],
    ) -> dict[str, Any]:
        """Return a ready TutorContent dict."""
        with propagate_attributes(
            session_id=session_id,
            metadata={
                "question_id": question_id,
                "question_number": package.get("number"),
                "provider": provider.name,
            },
            tags=["home-tutor", "tutor-analysis", provider.name],
        ):
            raw = await self._client.chat_json(
                provider,
                system_prompt=SYSTEM_PROMPT,
                user_prompt=build_user_prompt(package),
            )
            return normalize_llm_payload(
                session_id=session_id,
                question_id=question_id,
                payload=raw,
                model=provider.model,
            )


def make_generating_shell(session_id: str, question_id: str) -> dict[str, Any]:
    """Placeholder tutor document while LLM is running."""
    return _empty_tutor_shell(
        session_id=session_id,
        question_id=question_id,
        analysis_status="generating",
    )


def make_missing_shell(session_id: str, question_id: str) -> dict[str, Any]:
    """Placeholder when save-token mode has not run analysis yet."""
    return _empty_tutor_shell(
        session_id=session_id,
        question_id=question_id,
        analysis_status="missing",
    )


def make_failed_shell(
    session_id: str,
    question_id: str,
    *,
    error: str,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persisted failure state."""
    base = previous or _empty_tutor_shell(
        session_id=session_id,
        question_id=question_id,
        analysis_status="failed",
    )
    base["analysis_status"] = "failed"
    base["error"] = error
    return base


__all__ = ["LlmClientError", "TutorGenerator", "make_failed_shell", "make_generating_shell", "make_missing_shell", "normalize_llm_payload"]
