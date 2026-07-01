"""Incrementally update materialized packages when events arrive."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from home_tutor.services.analysis.materializer import build_question_package, build_timeline_index
from home_tutor.services.analysis.session_store import SessionStore

PackageUpdatedHook = Callable[[str, str, bool], None]


class PackageUpdater:
    """Apply events to persisted packages and timeline index."""

    def __init__(
        self,
        store: SessionStore,
        *,
        on_package_updated: PackageUpdatedHook | None = None,
    ) -> None:
        self._store = store
        self._on_package_updated = on_package_updated

    def rebuild_question_package(self, session_id: str, question_id: str) -> dict[str, Any]:
        """Rebuild one package by replaying all events for that question."""
        meta = self._store.read_meta(session_id)
        events = self._store.read_events(session_id)
        monolith_questions = self._load_question_defs(session_id)
        question = monolith_questions[question_id]
        regions = self._regions_for_question(session_id, question_id)

        package = build_question_package(
            session_id=session_id,
            question=question,
            regions=regions,
            events=events,
            grade_level=meta.get("grade_level", "primary"),
            subject=meta.get("subject", "math"),
        )
        package["status"] = "complete"
        self._store.write_package(session_id, question_id, package)
        if self._on_package_updated is not None:
            self._on_package_updated(session_id, question_id, False)
        return package

    def rebuild_timeline_index(self, session_id: str) -> dict[str, Any]:
        """Rebuild timeline index from all events and tutor verdicts."""
        meta = self._store.read_meta(session_id)
        events = self._store.read_events(session_id)
        question_numbers = {q["question_id"]: q["number"] for q in meta["questions"]}
        verdicts: dict[str, str] = {}
        for q in meta["questions"]:
            qid = q["question_id"]
            try:
                verdicts[qid] = self._store.read_tutor(session_id, qid)["verdict"]
            except FileNotFoundError:
                verdicts[qid] = "unknown"

        index = build_timeline_index(
            session_id=session_id,
            events=events,
            question_numbers=question_numbers,
            verdicts=verdicts,
        )
        self._store.write_timeline_index(session_id, index)
        return index

    def apply_event(self, session_id: str, event: dict[str, Any]) -> None:
        """Append event and refresh affected materialized views."""
        self._store.append_event(session_id, event)
        qid = event.get("question_id")
        if qid and event["type"] in {
            "answer.appeared",
            "answer.changed",
            "answer.erased",
            "question.focus",
            "question.blur",
            "idle.start",
            "idle.end",
        }:
            pkg = self.rebuild_question_package(session_id, qid)
            if event["type"].startswith("answer."):
                if self._on_package_updated is not None:
                    self._on_package_updated(session_id, qid, True)
                else:
                    self._mark_tutor_stale(session_id, qid)
        if event["type"] in {"question.focus", "question.blur", "session.end"}:
            self.rebuild_timeline_index(session_id)

    def _mark_tutor_stale(self, session_id: str, question_id: str) -> None:
        try:
            tutor = self._store.read_tutor(session_id, question_id)
        except FileNotFoundError:
            return
        tutor["stale"] = True
        self._store.write_tutor(session_id, question_id, tutor)

    def _load_question_defs(self, session_id: str) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for q in self._store.read_meta(session_id)["questions"]:
            qid = q["question_id"]
            pkg = self._store.read_package(session_id, qid)
            result[qid] = {
                "question_id": qid,
                "page_id": q["page_id"],
                "index_on_page": q["index_on_page"],
                "number": q["number"],
                "prompt_text": pkg["prompt"]["text"],
                "question_type": "unknown",
            }
        return result

    def _regions_for_question(self, session_id: str, question_id: str) -> list[dict[str, Any]]:
        pkg = self._store.read_package(session_id, question_id)
        layout = pkg.get("layout", {})
        regions = layout.get("regions", [])
        return [
            {
                "region_id": r["region_id"],
                "question_id": question_id,
                "role": r["role"],
                "bbox": r["bbox"],
            }
            for r in regions
        ]
