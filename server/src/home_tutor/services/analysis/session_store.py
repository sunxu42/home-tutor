"""Read and write split session directories."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SessionNotFoundError(FileNotFoundError):
    """Raised when no session directory matches session_id."""


def _truncate_text(text: str, max_len: int = 48) -> str:
    """Return a single-line preview suitable for timeline tooltips."""
    collapsed = " ".join(text.split())
    if len(collapsed) <= max_len:
        return collapsed
    return f"{collapsed[: max_len - 1]}…"


class SessionStore:
    """Filesystem-backed session store for fixture and local dev."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def resolve_session_dir(self, session_id: str) -> Path:
        """Find session directory by meta.json session_id."""
        if not self._root.is_dir():
            raise SessionNotFoundError(f"Sessions root not found: {self._root}")

        for child in self._root.iterdir():
            if not child.is_dir():
                continue
            meta_path = child / "meta.json"
            if not meta_path.is_file():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("session_id") == session_id:
                return child

        raise SessionNotFoundError(f"Session not found: {session_id}")

    def read_meta(self, session_id: str) -> dict[str, Any]:
        return json.loads((self.resolve_session_dir(session_id) / "meta.json").read_text(encoding="utf-8"))

    def read_timeline_index(self, session_id: str) -> dict[str, Any]:
        path = self.resolve_session_dir(session_id) / "timeline-index.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def read_package(self, session_id: str, question_id: str) -> dict[str, Any]:
        path = self.resolve_session_dir(session_id) / "packages" / f"{question_id}.json"
        if not path.is_file():
            raise FileNotFoundError(f"Package not found: {question_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def read_tutor(self, session_id: str, question_id: str) -> dict[str, Any]:
        path = self.resolve_session_dir(session_id) / "tutor" / f"{question_id}.json"
        if not path.is_file():
            raise FileNotFoundError(f"Tutor content not found: {question_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def read_events(self, session_id: str) -> list[dict[str, Any]]:
        path = self.resolve_session_dir(session_id) / "events.jsonl"
        events: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(json.loads(line))
        return events

    def append_event(self, session_id: str, event: dict[str, Any]) -> None:
        session_dir = self.resolve_session_dir(session_id)
        with (session_dir / "events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def write_package(self, session_id: str, question_id: str, package: dict[str, Any]) -> None:
        path = self.resolve_session_dir(session_id) / "packages" / f"{question_id}.json"
        path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")

    def write_timeline_index(self, session_id: str, index: dict[str, Any]) -> None:
        path = self.resolve_session_dir(session_id) / "timeline-index.json"
        path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    def write_tutor(self, session_id: str, question_id: str, tutor: dict[str, Any]) -> None:
        path = self.resolve_session_dir(session_id) / "tutor" / f"{question_id}.json"
        path.write_text(json.dumps(tutor, ensure_ascii=False, indent=2), encoding="utf-8")

    def build_tutor_view(self, session_id: str) -> dict[str, Any]:
        """Aggregate timeline index and per-question summaries for the review page."""
        meta = self.read_meta(session_id)
        index = self.read_timeline_index(session_id)

        questions = []
        for q in meta["questions"]:
            qid = q["question_id"]
            pkg = self.read_package(session_id, qid)
            tutor = self.read_tutor(session_id, qid)
            analysis_status = tutor.get("analysis_status", "ready")
            questions.append(
                {
                    "question_id": qid,
                    "number": q["number"],
                    "verdict": tutor["verdict"],
                    "active_duration_ms": pkg["process_metrics"]["active_duration_ms"],
                    "prompt_preview": _truncate_text(pkg.get("prompt", {}).get("text", "")),
                    "answer_preview": _truncate_text(pkg.get("final_answer", {}).get("text", "")),
                    "question_type": pkg.get("question_type", "unknown"),
                    "summary": _truncate_text(tutor.get("summary", ""), max_len=64),
                    "analysis_status": analysis_status,
                    "stale": bool(tutor.get("stale", False)),
                }
            )

        return {"timeline_index": index, "questions": questions}

    def build_question_detail(self, session_id: str, question_id: str) -> dict[str, Any]:
        """Return materialized package and tutor content for one question."""
        package = self.read_package(session_id, question_id)
        tutor = self.read_tutor(session_id, question_id)
        return {"package": package, "tutor": tutor}
