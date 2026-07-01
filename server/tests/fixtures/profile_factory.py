"""Build student profiles and answer sheets for mock fixtures."""

from __future__ import annotations

from exam_g6_final_2025 import (
    EXAM_QUESTIONS,
    AnswerStep,
    IdlePeriod,
    QuestionBehavior,
    StudentProfile,
)
from answer_sheets import _BASE_SHEETS, build_sheet
from exam_scoring import accuracy_percent, score_exam

TOTAL_POINTS = sum(question.max_score for question in EXAM_QUESTIONS)

PROFILE_SPECS: tuple[dict[str, object], ...] = (
    {
        "profile_id": "score48",
        "label": "小杰（状态不佳，约48分）",
        "target_score": 48,
        "duration_ms": 3_720_000,
        "session_id": "a1000000-0000-4000-8000-000000000000",
        "started_at": "2026-06-10T14:00:00.000Z",
        "base": "weak",
        "delta": {"q07": "√", "q29": "50%"},
    },
    {
        "profile_id": "score53",
        "label": "小杰（基础薄弱，约53分）",
        "target_score": 53,
        "duration_ms": 3_600_000,
        "session_id": "a1000001-0001-4001-8001-000000000001",
        "started_at": "2026-06-22T14:00:00.000Z",
        "base": "weak",
        "delta": {},
    },
    {
        "profile_id": "score58",
        "label": "小杰（一周后再练，约58分）",
        "target_score": 58,
        "duration_ms": 3_540_000,
        "session_id": "a1000002-0002-4002-8002-000000000002",
        "started_at": "2026-06-25T15:00:00.000Z",
        "base": "weak",
        "delta": {
            "q01": "180",
            "q05": "425；400",
            "q13": "B",
            "q16": "A",
        },
    },
    {
        "profile_id": "score62",
        "label": "小杰（持续进步，约62分）",
        "target_score": 62,
        "duration_ms": 3_480_000,
        "session_id": "a1000003-0003-4003-8003-000000000003",
        "started_at": "2026-06-29T16:30:00.000Z",
        "base": "weak",
        "delta": {
            "q01": "180",
            "q02": "30；24",
            "q04": "6；18.84；28.26",
            "q05": "425；400",
            "q13": "B",
            "q16": "A",
            "q22": "12.5cm²",
        },
    },
    {
        "profile_id": "score68",
        "label": "小雨（发挥一般，约68分）",
        "target_score": 68,
        "duration_ms": 3_660_000,
        "session_id": "b2000001-0001-4001-8001-000000000001",
        "started_at": "2026-06-15T13:30:00.000Z",
        "base": "medium",
        "delta": {"q06": "19", "q18": "C", "q20": "① 4  ② -13/24  ③ 55  ④ 1/8", "q28": "① 6962.5m²  ② 357m  ③ 7.5m"},
    },
    {
        "profile_id": "score73",
        "label": "小雨（中等稳定，约73分）",
        "target_score": 73,
        "duration_ms": 3_600_000,
        "session_id": "b2000002-0002-4002-8002-000000000002",
        "started_at": "2026-06-20T15:30:00.000Z",
        "base": "medium",
        "delta": {},
    },
    {
        "profile_id": "score78",
        "label": "小雨（状态回升，约78分）",
        "target_score": 78,
        "duration_ms": 3_540_000,
        "session_id": "b2000003-0003-4003-8003-000000000003",
        "started_at": "2026-06-27T14:15:00.000Z",
        "base": "medium",
        "delta": {
            "q06": "25",
            "q14": "D",
            "q18": "A",
            "q20": "① 4  ② -13/24  ③ 63  ④ 1/8",
            "q28": "① 6962.5m²  ② 357m  ③ 7.536m",
        },
    },
    {
        "profile_id": "score85",
        "label": "晨晨（粗心失误，约85分）",
        "target_score": 85,
        "duration_ms": 3_420_000,
        "session_id": "c3000001-0001-4001-8001-000000000001",
        "started_at": "2026-06-24T10:00:00.000Z",
        "base": "strong",
        "delta": {
            "q17": "A",
            "q20": "① 4  ② -13/24  ③ 63  ④ 3/16",
            "q28": "① 6962.5m²  ② 357m  ③ 7.54m",
            "q30": "B15% D34% 共400人",
        },
    },
    {
        "profile_id": "score92",
        "label": "晨晨（优秀，约92分）",
        "target_score": 92,
        "duration_ms": 3_480_000,
        "session_id": "c3000002-0002-4002-8002-000000000002",
        "started_at": "2026-06-18T16:00:00.000Z",
        "base": "strong",
        "delta": {},
    },
    {
        "profile_id": "score96",
        "label": "晨晨（最佳状态，约96分）",
        "target_score": 96,
        "duration_ms": 3_300_000,
        "session_id": "c3000003-0003-4003-8003-000000000003",
        "started_at": "2026-06-16T09:30:00.000Z",
        "base": "strong",
        "delta": {"q30": "B15% D35% 共400人"},
    },
)

_TIMING_BY_DIFFICULTY = {
    "easy": 70_000,
    "medium": 140_000,
    "hard": 280_000,
}

_STUCK_QUESTIONS = frozenset({"q06", "q14", "q20", "q26", "q28", "q30"})


def build_answer_sheet(spec: dict[str, object]) -> dict[str, str]:
    """Merge base answer sheet with per-profile overrides."""
    return build_sheet(str(spec["base"]), dict(spec.get("delta", {})))


def _scratch_for_answer(question_id: str, final_answer: str) -> tuple[AnswerStep, ...]:
    """Create lightweight scratch steps that hint at the student's thinking."""
    if question_id == "q01" and final_answer == "210":
        return (AnswerStep(8_000, "126+84", "scratch"), AnswerStep(45_000, "210", "scratch"))
    if question_id == "q01" and final_answer == "180":
        return (AnswerStep(8_000, "126+84=210", "scratch"), AnswerStep(40_000, "210×6/7", "scratch"))
    if question_id == "q20":
        return (AnswerStep(60_000, "先算括号", "scratch"),)
    if question_id == "q28":
        return (AnswerStep(70_000, "πr²", "scratch"),)
    if "；" in final_answer:
        first = final_answer.split("；", maxsplit=1)[0]
        return (AnswerStep(25_000, first, "scratch"),)
    if len(final_answer) > 6:
        return (AnswerStep(20_000, final_answer[:6], "scratch"),)
    return ()


def _behavior_for_question(question_id: str, final_answer: str) -> QuestionBehavior:
    question = next(item for item in EXAM_QUESTIONS if item.question_id == question_id)
    duration = _TIMING_BY_DIFFICULTY[question.difficulty]
    if question_id in _STUCK_QUESTIONS:
        duration = int(duration * 1.35)

    scratch = _scratch_for_answer(question_id, final_answer)
    answer_offset = 55_000 if scratch else 25_000
    steps: list[AnswerStep] = list(scratch)
    steps.append(AnswerStep(answer_offset, final_answer, "answer", 0.92))

    idle: tuple[IdlePeriod, ...] = ()
    if question_id in _STUCK_QUESTIONS and final_answer != question.correct_answer:
        idle = (IdlePeriod(int(duration * 0.35), int(duration * 0.25)),)

    return QuestionBehavior(
        time_ms=duration,
        steps=tuple(steps),
        idle_periods=idle,
        revisit=question_id == "q28",
    )


def build_profile(spec: dict[str, object]) -> StudentProfile:
    """Materialize one student profile from declarative spec."""
    answers = build_answer_sheet(spec)
    earned = score_exam(answers, EXAM_QUESTIONS)
    target = int(spec["target_score"])
    behaviors = {
        question.question_id: _behavior_for_question(question.question_id, answers[question.question_id])
        for question in EXAM_QUESTIONS
    }
    return StudentProfile(
        profile_id=str(spec["profile_id"]),
        label=str(spec["label"]),
        target_score=target,
        duration_ms=int(spec["duration_ms"]),
        session_id=str(spec["session_id"]),
        started_at=str(spec["started_at"]),
        accuracy_percent=float(target),
        earned_score=earned,
        behaviors=behaviors,
    )


ALL_PROFILES: tuple[StudentProfile, ...] = tuple(build_profile(spec) for spec in PROFILE_SPECS)

PROFILE_BY_ID: dict[str, StudentProfile] = {profile.profile_id: profile for profile in ALL_PROFILES}

STUDENT_A = PROFILE_BY_ID["score53"]
STUDENT_B = PROFILE_BY_ID["score73"]
STUDENT_C = PROFILE_BY_ID["score92"]
