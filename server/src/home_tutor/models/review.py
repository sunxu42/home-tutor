"""Pydantic schemas for session review API."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Verdict(str, Enum):
    """Question correctness verdict."""

    CORRECT = "correct"
    WRONG = "wrong"
    UNKNOWN = "unknown"


class AnalysisStatus(str, Enum):
    """LLM tutor analysis lifecycle status."""

    MISSING = "missing"
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class QuestionType(str, Enum):
    """Question classification."""

    FILL_BLANK = "fill_blank"
    MULTIPLE_CHOICE = "multiple_choice"
    CALCULATION = "calculation"
    WORD_PROBLEM = "word_problem"
    UNKNOWN = "unknown"


class ErrorCategory(str, Enum):
    """Error classification category."""

    CORRECT = "correct"
    CONCEPT_ERROR = "concept_error"
    CALCULATION_ERROR = "calculation_error"
    INCOMPLETE = "incomplete"
    UNKNOWN = "unknown"


class DataSource(str, Enum):
    """Session data source for analysis policy."""

    MOCK = "mock"
    LIVE = "live"


class ChoiceOption(BaseModel):
    """Multiple-choice option."""

    key: str
    text: str


class TimelineSegment(BaseModel):
    """One segment on the session timeline bar."""

    question_id: str
    number: int
    start_ms: int
    end_ms: int
    verdict: Verdict


class SessionTimelineIndex(BaseModel):
    """Precomputed timeline for the review progress bar."""

    model_config = ConfigDict(extra="allow")

    schema_version: str
    session_id: str
    duration_ms: int
    segments: list[TimelineSegment]


class QuestionSummary(BaseModel):
    """Per-question summary for tutor-view."""

    question_id: str
    number: int
    verdict: Verdict
    active_duration_ms: int
    prompt_preview: str
    answer_preview: str
    summary: str
    analysis_status: AnalysisStatus
    stale: bool
    question_type: QuestionType | str = QuestionType.UNKNOWN


class TutorAnalysisPolicyResponse(BaseModel):
    """Resolved LLM analysis policy exposed to the client."""

    data_source: DataSource
    manual_only: bool
    prefetch_on_select: bool
    auto_analyze_on_view: bool


class TutorViewBase(BaseModel):
    """Timeline and question summaries without runtime analysis policy."""

    timeline_index: SessionTimelineIndex
    questions: list[QuestionSummary]


class TutorViewResponse(TutorViewBase):
    """Aggregate view for the session review page header and timeline."""

    analysis_policy: TutorAnalysisPolicyResponse


class ErrorClassification(BaseModel):
    """Structured error classification from LLM."""

    model_config = ConfigDict(extra="allow")

    category: ErrorCategory
    subcategory: str | None = None
    confidence: float | None = None


class TutorAction(BaseModel):
    """Suggested tutor action button."""

    id: str
    label: str
    enabled: bool


class TutorContent(BaseModel):
    """Per-question tutoring copy."""

    model_config = ConfigDict(extra="allow")

    schema_version: str
    question_id: str
    analysis_status: AnalysisStatus
    verdict: Verdict
    reference_answer: str
    summary: str
    explanation_paragraphs: list[str]
    session_id: str | None = None
    error_classification: ErrorClassification | None = None
    process_comment: str | None = None
    actions: list[TutorAction] | None = None
    stale: bool | None = None
    generated_at: str | None = None
    model: str | None = None
    error: str | None = None


class QuestionProcessPackage(BaseModel):
    """Materialized per-question package for review and LLM."""

    model_config = ConfigDict(extra="allow")

    schema_version: str
    session_id: str
    question_id: str
    number: int | None = None
    question_type: QuestionType | str | None = None
    status: str | None = None
    prompt: dict[str, Any]
    final_answer: dict[str, Any]
    answer_timeline: list[dict[str, Any]] = Field(default_factory=list)
    focus_segments: list[dict[str, Any]] = Field(default_factory=list)
    process_metrics: dict[str, Any]
    scratch_work: list[dict[str, Any]] | None = None


class QuestionDetailResponse(BaseModel):
    """Full package and tutor content for one question."""

    package: QuestionProcessPackage
    tutor: TutorContent


class AnalyzeQuestionResponse(BaseModel):
    """Response from manual analyze trigger."""

    analysis_status: AnalysisStatus | str
