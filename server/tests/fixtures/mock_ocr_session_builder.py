"""从学生作答画像构建 events-only 的 OcrSessionRecord JSON。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from exam_g6_final_2025 import (
    EXAM_PAGES,
    EXAM_QUESTIONS,
    ExamQuestion,
    StudentProfile,
)
from profile_factory import ALL_PROFILES


@dataclass
class _Counters:
    evt: int = 0
    frame: int = 0


def _evt_id(counter: int) -> str:
    return f"evt_{counter:05d}"


def _frame_id(counter: int) -> str:
    return f"frame_{counter:05d}"


def _bbox_for_question(q: ExamQuestion) -> dict[str, float]:
    """按页内题号生成归一化 bbox（mock 用，非真实 OCR 坐标）。"""
    row = (q.index_on_page - 1) % 6
    col = (q.index_on_page - 1) // 6
    base_y = 0.08 + row * 0.14
    base_x = 0.05 + col * 0.48
    return {"x": round(base_x, 3), "y": round(base_y, 3), "w": 0.42, "h": 0.10}


def _answer_bbox(prompt_bbox: dict[str, float]) -> dict[str, float]:
    return {
        "x": round(prompt_bbox["x"] + prompt_bbox["w"] * 0.55, 3),
        "y": round(prompt_bbox["y"] + prompt_bbox["h"] * 0.55, 3),
        "w": 0.18,
        "h": 0.04,
    }


def _scratch_bbox(prompt_bbox: dict[str, float]) -> dict[str, float]:
    return {
        "x": round(prompt_bbox["x"] + 0.02, 3),
        "y": round(prompt_bbox["y"] + prompt_bbox["h"] * 0.25, 3),
        "w": 0.35,
        "h": 0.06,
    }


def _iso_at(start: datetime, offset_ms: int) -> str:
    return (start + timedelta(milliseconds=offset_ms)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _schedule_question_times(
    profile: StudentProfile,
    gap_between_ms: int = 8_000,
    page_turn_ms: int = 25_000,
) -> dict[str, tuple[int, int]]:
    """将各题 time_ms 排入会话时间轴，插入翻页间隔。"""
    schedule: dict[str, tuple[int, int]] = {}
    cursor = 15_000
    prev_page: str | None = None

    for q in EXAM_QUESTIONS:
        behavior = profile.behaviors[q.question_id]
        if prev_page is not None and q.page_id != prev_page:
            cursor += page_turn_ms
        start = cursor
        end = start + behavior.time_ms
        schedule[q.question_id] = (start, end)
        cursor = end + gap_between_ms
        prev_page = q.page_id

    return schedule


def _scale_schedule(
    schedule: dict[str, tuple[int, int]],
    target_duration_ms: int,
) -> dict[str, tuple[int, int]]:
    """缩放时间轴使最后一题结束时间贴近目标总时长。"""
    if not schedule:
        return schedule
    last_end = max(end for _, end in schedule.values())
    usable = target_duration_ms - 20_000
    if last_end <= usable:
        return schedule
    ratio = usable / last_end
    return {qid: (int(s * ratio), int(e * ratio)) for qid, (s, e) in schedule.items()}


def build_ocr_session(profile: StudentProfile) -> dict[str, Any]:
    """构建 events-only 的 OcrSessionRecord。"""
    started = datetime.fromisoformat(profile.started_at.replace("Z", "+00:00"))
    schedule = _scale_schedule(_schedule_question_times(profile), profile.duration_ms)

    questions: list[dict[str, Any]] = []
    regions: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    frames: list[dict[str, Any]] = []
    counters = _Counters()

    exam_source = "人教版2025-2026学年小学六年级数学上册期末测试卷.docx"

    for q in EXAM_QUESTIONS:
        bbox = _bbox_for_question(q)
        prompt_rid = f"r_prompt_{q.question_id}"
        answer_rid = f"r_answer_{q.question_id}"
        scratch_rid = f"r_scratch_{q.question_id}"

        questions.append(
            {
                "question_id": q.question_id,
                "page_id": q.page_id,
                "index_on_page": q.index_on_page,
                "prompt_text": q.prompt_text,
                "prompt_region_ids": [prompt_rid],
                "answer_region_ids": [answer_rid],
                "question_type": q.question_type,
                **(
                    {
                        "options": [
                            {"key": choice.key, "text": choice.text} for choice in q.choices
                        ]
                    }
                    if q.choices
                    else {}
                ),
            }
        )
        regions.extend(
            [
                {
                    "region_id": prompt_rid,
                    "question_id": q.question_id,
                    "role": "printed_prompt",
                    "bbox": bbox,
                },
                {
                    "region_id": answer_rid,
                    "question_id": q.question_id,
                    "role": "student_answer",
                    "bbox": _answer_bbox(bbox),
                },
                {
                    "region_id": scratch_rid,
                    "question_id": q.question_id,
                    "role": "scratch_work",
                    "bbox": _scratch_bbox(bbox),
                },
            ]
        )

    def add_frame(t_ms: int, page_id: str) -> str:
        counters.frame += 1
        fid = _frame_id(counters.frame)
        frames.append(
            {
                "frame_id": fid,
                "t_offset_ms": t_ms,
                "captured_at": _iso_at(started, t_ms),
                "image_uri": f"mock://sessions/{profile.session_id}/frames/{fid}.jpg",
                "page_id": page_id,
            }
        )
        return fid

    def add_event(
        event_type: str,
        t_ms: int,
        *,
        question_id: str | None = None,
        region_id: str | None = None,
        page_id: str | None = None,
        frame_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        counters.evt += 1
        evt: dict[str, Any] = {
            "event_id": _evt_id(counters.evt),
            "type": event_type,
            "t_offset_ms": t_ms,
        }
        if frame_id:
            evt["frame_id"] = frame_id
        if question_id:
            evt["question_id"] = question_id
        if region_id:
            evt["region_id"] = region_id
        if page_id:
            evt["page_id"] = page_id
        if payload:
            evt["payload"] = payload
        events.append(evt)

    start_fid = add_frame(0, "page_1")
    add_event("session.start", 0, frame_id=start_fid)
    add_event("page.detected", 5_000, page_id="page_1", frame_id=start_fid)

    current_q: str | None = None
    detected_pages: set[str] = {"page_1"}

    for q in EXAM_QUESTIONS:
        behavior = profile.behaviors[q.question_id]
        q_start, _ = schedule[q.question_id]

        if q.page_id not in detected_pages:
            detected_pages.add(q.page_id)
            pfid = add_frame(max(0, q_start - 3_000), q.page_id)
            add_event(
                "page.detected",
                max(0, q_start - 3_000),
                page_id=q.page_id,
                frame_id=pfid,
            )

        if current_q and current_q != q.question_id:
            blur_fid = add_frame(q_start, q.page_id)
            add_event(
                "question.blur",
                q_start,
                question_id=current_q,
                page_id=q.page_id,
                frame_id=blur_fid,
                payload={"next_question_id": q.question_id},
            )

        focus_fid = add_frame(q_start + 500, q.page_id)
        add_event(
            "question.focus",
            q_start + 500,
            question_id=q.question_id,
            page_id=q.page_id,
            frame_id=focus_fid,
        )
        current_q = q.question_id

        answer_rid = f"r_answer_{q.question_id}"
        scratch_rid = f"r_scratch_{q.question_id}"

        for idle in behavior.idle_periods:
            idle_start = q_start + idle.offset_ms
            add_event(
                "idle.start",
                idle_start,
                question_id=q.question_id,
                page_id=q.page_id,
            )
            add_event(
                "idle.end",
                idle_start + idle.duration_ms,
                question_id=q.question_id,
                page_id=q.page_id,
                payload={"duration_ms": idle.duration_ms},
            )

        prev_answer = ""
        for step in behavior.steps:
            t_ms = q_start + step.offset_ms
            rid = answer_rid if step.region == "answer" else scratch_rid
            fid = add_frame(t_ms, q.page_id)

            if step.region == "answer" and not prev_answer:
                add_event(
                    "answer.appeared",
                    t_ms,
                    question_id=q.question_id,
                    region_id=rid,
                    page_id=q.page_id,
                    frame_id=fid,
                    payload={"text": step.text, "confidence": step.confidence},
                )
                prev_answer = step.text
            elif step.region == "answer":
                add_event(
                    "answer.changed",
                    t_ms,
                    question_id=q.question_id,
                    region_id=rid,
                    page_id=q.page_id,
                    frame_id=fid,
                    payload={
                        "text": step.text,
                        "prev_text": prev_answer,
                        "confidence": step.confidence,
                    },
                )
                prev_answer = step.text
            else:
                add_event(
                    "answer.appeared",
                    t_ms,
                    question_id=q.question_id,
                    region_id=rid,
                    page_id=q.page_id,
                    frame_id=fid,
                    payload={"text": step.text, "confidence": step.confidence},
                )

    last_q = EXAM_QUESTIONS[-1].question_id
    end_t = profile.duration_ms - 5_000
    end_fid = add_frame(end_t, "page_4")
    add_event(
        "question.blur",
        end_t - 2_000,
        question_id=last_q,
        page_id="page_4",
        frame_id=end_fid,
    )
    add_event("session.end", end_t, frame_id=end_fid)

    return {
        "schema_version": "home-tutor.ocr-session.v1",
        "session_id": profile.session_id,
        "grade_level": "primary",
        "subject": "math",
        "started_at": started.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "ended_at": _iso_at(started, end_t),
        "pages": list(EXAM_PAGES),
        "questions": questions,
        "regions": regions,
        "frames": frames,
        "events": events,
        "metadata": {
            "mock": True,
            "storage_model": "events-only",
            "student_profile": profile.profile_id,
            "student_label": profile.label,
            "target_score": profile.target_score,
            "exam_source": exam_source,
            "duration_minutes": round(profile.duration_ms / 60_000, 1),
        },
    }


def write_session(profile: StudentProfile, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    session = build_ocr_session(profile)
    out_path = output_dir / f"g6-math-final-{profile.profile_id}.json"
    out_path.write_text(
        json.dumps(session, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out_path


def main() -> None:
    out = Path(__file__).resolve().parent / "ocr-sessions"
    for profile in ALL_PROFILES:
        path = write_session(profile, out)
        size_kb = path.stat().st_size / 1024
        print(f"Wrote {path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
