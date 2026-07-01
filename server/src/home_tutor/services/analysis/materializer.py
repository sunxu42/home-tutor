"""Materialize SessionTimelineIndex and QuestionProcessPackage from events."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def build_timeline_index(
    *,
    session_id: str,
    events: list[dict[str, Any]],
    question_numbers: dict[str, int],
    verdicts: dict[str, str],
) -> dict[str, Any]:
    """Build SessionTimelineIndex from session events."""
    open_focus: dict[str, int] = {}
    segments: list[dict[str, Any]] = []
    duration_ms = 0

    for evt in sorted(events, key=lambda e: e["t_offset_ms"]):
        t = int(evt["t_offset_ms"])
        duration_ms = max(duration_ms, t)
        qid = evt.get("question_id")
        if evt["type"] == "question.focus" and qid:
            open_focus[qid] = t
        elif evt["type"] == "question.blur" and qid and qid in open_focus:
            segments.append(
                {
                    "question_id": qid,
                    "number": question_numbers[qid],
                    "start_ms": open_focus.pop(qid),
                    "end_ms": t,
                    "verdict": verdicts.get(qid, "unknown"),
                }
            )
        elif evt["type"] == "session.end":
            duration_ms = t

    return {
        "schema_version": "home-tutor.session-timeline-index.v1",
        "session_id": session_id,
        "duration_ms": max(duration_ms, 1),
        "segments": segments,
    }


def _answer_region_id(question_id: str) -> str:
    return f"r_answer_{question_id}"


def _scratch_region_id(question_id: str) -> str:
    return f"r_scratch_{question_id}"


def build_question_package(
    *,
    session_id: str,
    question: dict[str, Any],
    regions: list[dict[str, Any]],
    events: list[dict[str, Any]],
    grade_level: str = "primary",
    subject: str = "math",
) -> dict[str, Any]:
    """Build a materialized QuestionProcessPackage for one question."""
    qid = question["question_id"]
    q_events = [e for e in sorted(events, key=lambda e: e["t_offset_ms"]) if e.get("question_id") == qid]

    answer_timeline: list[dict[str, Any]] = []
    scratch_work: list[dict[str, Any]] = []
    final_answer_text = ""
    final_confidence: float | None = None
    revision_count = 0

    open_focus: int | None = None
    focus_segments: list[dict[str, Any]] = []
    idle_periods: list[dict[str, Any]] = []
    open_idle_start: int | None = None

    key_moments: list[dict[str, Any]] = []

    for evt in q_events:
        t = int(evt["t_offset_ms"])
        payload = evt.get("payload") or {}

        if evt["type"] == "question.focus":
            open_focus = t
        elif evt["type"] == "question.blur" and open_focus is not None:
            focus_segments.append(
                {
                    "segment_index": len(focus_segments) + 1,
                    "start_ms": open_focus,
                    "end_ms": t,
                    "duration_ms": t - open_focus,
                }
            )
            open_focus = None
        elif evt["type"] == "idle.start":
            open_idle_start = t
        elif evt["type"] == "idle.end" and open_idle_start is not None:
            idle_periods.append(
                {
                    "start_ms": open_idle_start,
                    "end_ms": t,
                    "duration_ms": int(payload.get("duration_ms", t - open_idle_start)),
                }
            )
            open_idle_start = None
        elif evt["type"] in ("answer.appeared", "answer.changed", "answer.erased"):
            region_id = evt.get("region_id", "")
            text = str(payload.get("text", ""))
            confidence = payload.get("confidence")
            frame_id = evt.get("frame_id")

            if region_id == _scratch_region_id(qid):
                scratch_work.append(
                    {
                        "text": text,
                        "region_id": region_id,
                        "confidence": confidence,
                    }
                )
                continue

            if region_id != _answer_region_id(qid):
                continue

            if evt["type"] == "answer.appeared":
                kind = "appeared"
            elif evt["type"] == "answer.changed":
                kind = "changed"
                revision_count += 1
            else:
                kind = "erased"
                revision_count += 1

            entry: dict[str, Any] = {
                "t_offset_ms": t,
                "kind": kind,
                "text": text,
            }
            if evt["type"] == "answer.changed":
                entry["prev_text"] = payload.get("prev_text", "")
            if frame_id:
                entry["frame_id"] = frame_id
            if confidence is not None:
                entry["confidence"] = confidence

            answer_timeline.append(entry)
            if kind != "erased":
                final_answer_text = text
                if confidence is not None:
                    final_confidence = float(confidence)
                key_moments = [
                    {
                        "label": "final_answer",
                        "t_offset_ms": t,
                        "frame_id": frame_id,
                    }
                ]

    active_duration_ms = sum(seg["duration_ms"] for seg in focus_segments)
    first_touch_ms = focus_segments[0]["start_ms"] if focus_segments else None
    last_change_ms = (
        answer_timeline[-1]["t_offset_ms"] if answer_timeline else first_touch_ms
    )

    layout_regions = [
        {
            "region_id": r["region_id"],
            "role": r["role"],
            "bbox": r["bbox"],
        }
        for r in regions
        if r.get("question_id") == qid
    ]

    final_answer: dict[str, Any] = {"text": final_answer_text}
    if final_confidence is not None:
        final_answer["confidence"] = final_confidence

    prompt: dict[str, Any] = {"text": question["prompt_text"]}
    options = question.get("options")
    if options:
        prompt["options"] = options

    now = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    return {
        "schema_version": "home-tutor.question-package.v1",
        "session_id": session_id,
        "question_id": qid,
        "grade_level": grade_level,
        "subject": subject,
        "page_id": question["page_id"],
        "index_on_page": question["index_on_page"],
        "number": question["number"],
        "question_type": question.get("question_type", "unknown"),
        "status": "complete",
        "updated_at": now,
        "prompt": prompt,
        "layout": {"regions": layout_regions},
        "answer_timeline": answer_timeline,
        "final_answer": final_answer,
        "focus_segments": focus_segments,
        "process_metrics": {
            "first_touch_ms": first_touch_ms,
            "last_change_ms": last_change_ms,
            "active_duration_ms": active_duration_ms,
            "idle_periods_ms": idle_periods,
            "revision_count": revision_count,
            "stuck": len(idle_periods) > 0,
        },
        "scratch_work": scratch_work,
        "key_moments": key_moments,
    }
