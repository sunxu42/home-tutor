"""Orchestrate per-question LLM tutor analysis with SSE notifications."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from home_tutor.core.config import settings
from home_tutor.core.logging import get_logger, log_milestone
from home_tutor.services.analysis.session_store import SessionNotFoundError, SessionStore
from home_tutor.services.llm.client import LlmClient
from home_tutor.services.llm.config import LlmSettings, load_llm_settings
from home_tutor.services.llm.tutor_analysis_policy import TutorAnalysisPolicy
from home_tutor.services.llm.tutor_generator import (
    LlmClientError,
    TutorGenerator,
    make_failed_shell,
    make_generating_shell,
    make_missing_shell,
)

logger = get_logger(__name__)

QuestionKey = tuple[str, str]


@dataclass
class SseEvent:
    """Server-sent event payload."""

    event: str
    data: dict[str, Any]


@dataclass
class TutorAnalysisService:
    """Schedule and run LLM analysis; broadcast SSE to subscribers."""

    store: SessionStore
    llm_settings: LlmSettings = field(default_factory=load_llm_settings)
    generator: TutorGenerator | None = None

    def __post_init__(self) -> None:
        self._inflight: set[QuestionKey] = set()
        self._subscribers: dict[QuestionKey, list[asyncio.Queue[SseEvent | None]]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        if self.generator is None:
            self.generator = TutorGenerator(
                LlmClient(timeout_sec=self.llm_settings.request_timeout_sec)
            )

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Remember the running event loop for sync enqueue from PackageUpdater."""
        self._loop = loop

    def _key(self, session_id: str, question_id: str) -> QuestionKey:
        return (session_id, question_id)

    def _policy_for(self, session_id: str) -> TutorAnalysisPolicy:
        meta = self.store.read_meta(session_id)
        return TutorAnalysisPolicy.for_session(
            meta,
            save_token_mode=self.llm_settings.save_token_mode,
        )

    def build_analysis_policy(self, meta: dict[str, Any]) -> TutorAnalysisPolicy:
        """Expose resolved policy for API responses."""
        return TutorAnalysisPolicy.for_session(
            meta,
            save_token_mode=self.llm_settings.save_token_mode,
        )

    def _should_skip_existing(self, session_id: str, question_id: str, *, force: bool) -> bool:
        if force:
            return False
        policy = self._policy_for(session_id)
        tutor = self._read_tutor_or_none(session_id, question_id)
        if policy.should_skip_schedule(tutor, force=force):
            return True
        if policy.is_mock:
            return False
        if not self.llm_settings.skip_fixture_tutor:
            return False
        if tutor is None:
            return False
        status = tutor.get("analysis_status", "ready")
        return status == "ready" and not tutor.get("stale", False)

    def _read_tutor_or_none(self, session_id: str, question_id: str) -> dict[str, Any] | None:
        try:
            return self.store.read_tutor(session_id, question_id)
        except FileNotFoundError:
            return None

    def enqueue(
        self,
        session_id: str,
        question_id: str,
        *,
        reason: str,
        force: bool = False,
    ) -> None:
        """Thread-safe entry from sync code (PackageUpdater)."""
        if self._loop is None:
            logger.debug(
                "analysis_enqueue_skipped",
                session_id=session_id,
                question_id=question_id,
                reason="loop_not_bound",
            )
            return
        self._loop.call_soon_threadsafe(
            lambda: asyncio.create_task(
                self.schedule(session_id, question_id, reason=reason, force=force)
            )
        )

    async def schedule(
        self,
        session_id: str,
        question_id: str,
        *,
        reason: str,
        force: bool = False,
    ) -> str:
        """Queue analysis if allowed; return resulting analysis_status."""
        key = self._key(session_id, question_id)
        if key in self._inflight:
            return "generating"

        if self._should_skip_existing(session_id, question_id, force=force):
            tutor = self._read_tutor_or_none(session_id, question_id)
            return str(tutor.get("analysis_status", "ready")) if tutor else "ready"

        policy = self._policy_for(session_id)
        if policy.should_write_missing_on_schedule(force=force):
            shell = make_missing_shell(session_id, question_id)
            self.store.write_tutor(session_id, question_id, shell)
            return "missing"

        if not force and policy.is_mock:
            tutor = self._read_tutor_or_none(session_id, question_id)
            return str(tutor.get("analysis_status", "ready")) if tutor else "missing"

        if not self.llm_settings.is_configured():
            failed = make_failed_shell(
                session_id,
                question_id,
                error="LLM provider not configured",
                previous=self._read_tutor_or_none(session_id, question_id),
            )
            self.store.write_tutor(session_id, question_id, failed)
            await self._broadcast(key, SseEvent("error", {"analysis_status": "failed", "error": failed["error"]}))
            return "failed"

        self._inflight.add(key)
        generating = make_generating_shell(session_id, question_id)
        self.store.write_tutor(session_id, question_id, generating)
        await self._broadcast(key, SseEvent("status", {"analysis_status": "generating"}))

        log_milestone(
            logger,
            "ANALYSIS_ENQUEUED",
            session_id=session_id,
            question_id=question_id,
            reason=reason,
        )
        asyncio.create_task(self._run(session_id, question_id, reason=reason))
        return "generating"

    async def _run(self, session_id: str, question_id: str, *, reason: str) -> None:
        key = self._key(session_id, question_id)
        try:
            log_milestone(
                logger,
                "ANALYSIS_STARTED",
                session_id=session_id,
                question_id=question_id,
                reason=reason,
            )
            package = self.store.read_package(session_id, question_id)
            provider = self.llm_settings.active()
            if provider is None:
                raise LlmClientError("LLM provider not configured")

            from langfuse import propagate_attributes

            with propagate_attributes(metadata={"analysis_reason": reason}):
                tutor = await self.generator.generate(
                    provider,
                    session_id=session_id,
                    question_id=question_id,
                    package=package,
                )
            self.store.write_tutor(session_id, question_id, tutor)
            await self._broadcast(key, SseEvent("tutor", tutor))
            log_milestone(
                logger,
                "ANALYSIS_COMPLETE",
                session_id=session_id,
                question_id=question_id,
                reason=reason,
                verdict=tutor.get("verdict"),
            )
        except (SessionNotFoundError, FileNotFoundError) as exc:
            log_milestone(
                logger,
                "ANALYSIS_FAILED",
                session_id=session_id,
                question_id=question_id,
                error=str(exc),
            )
            failed = make_failed_shell(session_id, question_id, error=str(exc))
            self.store.write_tutor(session_id, question_id, failed)
            await self._broadcast(key, SseEvent("error", {"analysis_status": "failed", "error": str(exc)}))
        except LlmClientError as exc:
            log_milestone(
                logger,
                "ANALYSIS_FAILED",
                session_id=session_id,
                question_id=question_id,
                error=str(exc),
            )
            failed = make_failed_shell(
                session_id,
                question_id,
                error=str(exc),
                previous=self._read_tutor_or_none(session_id, question_id),
            )
            self.store.write_tutor(session_id, question_id, failed)
            await self._broadcast(key, SseEvent("error", {"analysis_status": "failed", "error": str(exc)}))
        except Exception as exc:
            logger.exception(
                "analysis_unexpected_failure",
                session_id=session_id,
                question_id=question_id,
            )
            log_milestone(
                logger,
                "ANALYSIS_FAILED",
                session_id=session_id,
                question_id=question_id,
                error="Internal analysis error",
            )
            failed = make_failed_shell(session_id, question_id, error="Internal analysis error")
            self.store.write_tutor(session_id, question_id, failed)
            await self._broadcast(key, SseEvent("error", {"analysis_status": "failed", "error": str(exc)}))
        finally:
            self._inflight.discard(key)

    def on_package_updated(
        self,
        session_id: str,
        question_id: str,
        *,
        answer_changed: bool,
    ) -> None:
        """Hook from PackageUpdater after package materialization."""
        policy = self._policy_for(session_id)

        if policy.is_mock:
            return

        if self.llm_settings.save_token_mode:
            if answer_changed:
                tutor = self._read_tutor_or_none(session_id, question_id)
                if tutor is not None:
                    tutor["stale"] = True
                    self.store.write_tutor(session_id, question_id, tutor)
            else:
                shell = make_missing_shell(session_id, question_id)
                existing = self._read_tutor_or_none(session_id, question_id)
                if existing is None:
                    self.store.write_tutor(session_id, question_id, shell)
            return

        self.enqueue(
            session_id,
            question_id,
            reason="package_updated_stale" if answer_changed else "package_ready",
            force=answer_changed,
        )

    async def subscribe(self, session_id: str, question_id: str) -> AsyncIterator[SseEvent]:
        """Yield SSE events for one question until terminal state."""
        key = self._key(session_id, question_id)
        queue: asyncio.Queue[SseEvent | None] = asyncio.Queue()
        self._subscribers.setdefault(key, []).append(queue)

        tutor = self._read_tutor_or_none(session_id, question_id)
        if tutor is not None:
            status = tutor.get("analysis_status", "ready")
            if status == "ready" and not tutor.get("stale"):
                yield SseEvent("tutor", tutor)
                return
            if status == "failed":
                yield SseEvent("error", {"analysis_status": "failed", "error": tutor.get("error")})
                return
            if status in {"generating", "pending"}:
                yield SseEvent("status", {"analysis_status": status})

        try:
            while True:
                event = await asyncio.wait_for(queue.get(), timeout=60.0)
                if event is None:
                    break
                yield event
                if event.event in {"tutor", "error"}:
                    break
        except TimeoutError:
            yield SseEvent("status", {"analysis_status": "generating"})
        finally:
            subs = self._subscribers.get(key, [])
            if queue in subs:
                subs.remove(queue)

    async def _broadcast(self, key: QuestionKey, event: SseEvent) -> None:
        for queue in self._subscribers.get(key, []):
            await queue.put(event)

    def ensure_on_view(self, session_id: str, question_id: str) -> None:
        """When review page opens a question, schedule if needed (eager mode)."""
        policy = self._policy_for(session_id)
        if policy.is_mock:
            return

        tutor = self._read_tutor_or_none(session_id, question_id)
        if tutor is None:
            if not self.llm_settings.save_token_mode:
                self.enqueue(session_id, question_id, reason="view_missing")
            return

        status = tutor.get("analysis_status", "ready")
        if status in {"missing", "failed"} or tutor.get("stale"):
            if not self.llm_settings.save_token_mode or tutor.get("stale"):
                self.enqueue(
                    session_id,
                    question_id,
                    reason="view_refresh",
                    force=status == "failed",
                )

    async def schedule_on_view_if_needed(
        self,
        session_id: str,
        question_id: str,
        tutor: dict[str, Any],
    ) -> None:
        """Async wrapper used by HTTP handlers after loading tutor."""
        policy = self._policy_for(session_id)
        if not policy.should_auto_analyze_on_view(tutor):
            return
        status = tutor.get("analysis_status", "ready")
        await self.schedule(
            session_id,
            question_id,
            reason="view",
            force=status == "failed" or bool(tutor.get("stale")),
        )


_service: TutorAnalysisService | None = None


def get_analysis_service() -> TutorAnalysisService:
    """Return the process-wide analysis service singleton."""
    global _service
    if _service is None:
        _service = TutorAnalysisService(store=SessionStore(settings.session_fixtures_root))
    return _service


def format_sse(event: SseEvent) -> str:
    """Format one SSE frame."""
    return f"event: {event.event}\ndata: {json.dumps(event.data, ensure_ascii=False)}\n\n"
