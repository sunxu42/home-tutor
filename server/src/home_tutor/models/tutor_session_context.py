"""Tutor session context for AG-UI chat rounds."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class NavigationContext(BaseModel):
    """Session navigation slice sent to the tutor chat agent."""

    question_index: int
    total_questions: int
    timeline_ms: int | None = None


class PackageContext(BaseModel):
    """Question package slice for chat context."""

    prompt_text: str
    options: list[dict[str, str]] | None = None
    final_answer: str
    question_type: str | None = None
    verdict: Literal["correct", "wrong", "unknown"]
    process_summary: str | None = None


class TutorContextSlice(BaseModel):
    """Existing tutor analysis slice."""

    summary: str
    error_category: str | None = None
    explanation_paragraphs: list[str]
    analysis_status: str


class A2UIContextSlice(BaseModel):
    """A2UI surface state."""

    surface_id: str
    data_model: dict[str, Any] = Field(default_factory=dict)
    recent_actions: list[dict[str, Any]] = Field(default_factory=list)


class TranscriptEntry(BaseModel):
    """One chat turn."""

    role: Literal["user", "assistant"]
    content: str
    source: Literal["asr", "text", "action"]
    ts: int


class VisionHint(BaseModel):
    """Metadata for an optional vision attachment."""

    region_id: str
    reason: str
    layout_hash: str


class TutorSessionContext(BaseModel):
    """Full structured context for one tutor chat round."""

    schema_version: Literal["home-tutor.tutor-session-context.v1"] = (
        "home-tutor.tutor-session-context.v1"
    )
    page: Literal["session_review"]
    session_id: str
    question_id: str
    navigation: NavigationContext
    package: PackageContext
    tutor: TutorContextSlice
    a2ui: A2UIContextSlice
    transcript: list[TranscriptEntry] = Field(default_factory=list)
    vision_hints: list[VisionHint] | None = None
