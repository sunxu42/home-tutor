"""Exam scoring utilities for mock session fixtures."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from exam_g6_final_2025 import ExamQuestion

_NORMALIZE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """Collapse whitespace for answer comparison."""
    return _NORMALIZE_RE.sub("", text).lower()


def split_parts(text: str) -> list[str]:
    """Split multi-blank answers on Chinese or ASCII semicolons."""
    return [part.strip() for part in re.split(r"[；;]", text) if part.strip()]


def score_parts(student: str, reference: str, max_score: int) -> float:
    """Award proportional credit for multi-part answers."""
    student_parts = split_parts(student)
    reference_parts = split_parts(reference)
    if not reference_parts:
        return float(max_score) if normalize_text(student) == normalize_text(reference) else 0.0
    if not student_parts:
        return 0.0
    per_part = max_score / len(reference_parts)
    earned = 0.0
    for index, ref_part in enumerate(reference_parts):
        student_part = student_parts[index] if index < len(student_parts) else ""
        if normalize_text(student_part) == normalize_text(ref_part):
            earned += per_part
    return earned


def score_sub_items(student: str, reference: str, max_score: int) -> float:
    """Score calculation items marked with ①②③④."""
    ref_items = re.findall(r"[①②③④]\s*([^①②③④]+)", reference)
    student_items = re.findall(r"[①②③④]\s*([^①②③④]+)", student)
    if not ref_items:
        return score_parts(student, reference, max_score)
    if not student_items:
        return 0.0
    per_item = max_score / len(ref_items)
    earned = 0.0
    for index, ref_item in enumerate(ref_items):
        student_item = student_items[index] if index < len(student_items) else ""
        if normalize_text(student_item) == normalize_text(ref_item.strip()):
            earned += per_item
    return earned


def score_drawing_answer(student: str, max_score: int) -> float:
    """Heuristic rubric for free-form drawing answers."""
    if not student.strip():
        return 0.0
    if "完成" in student:
        return float(max_score)
    if "已画" in student or "路线图" in student:
        return float(max_score) * 0.75
    if "未标" in student or "偏角" in student or "线段" in student:
        return float(max_score) * 0.25
    return float(max_score) * 0.5


def score_answer(question: ExamQuestion, student_answer: str) -> float:
    """Return earned points for one question."""
    if not student_answer.strip():
        return 0.0

    if question.question_id == "q23":
        return score_drawing_answer(student_answer, question.max_score)

    if question.question_type == "multiple_choice":
        return (
            float(question.max_score)
            if normalize_text(student_answer) == normalize_text(question.correct_answer)
            else 0.0
        )

    if question.question_id in {"q20", "q28"} or "①" in question.correct_answer:
        return score_sub_items(student_answer, question.correct_answer, question.max_score)

    if "；" in question.correct_answer or ";" in question.correct_answer:
        return score_parts(student_answer, question.correct_answer, question.max_score)

    if normalize_text(student_answer) == normalize_text(question.correct_answer):
        return float(question.max_score)

    # Allow minor formatting differences for unit answers.
    student_clean = student_answer.replace("cm²", "cm2").replace("m²", "m2")
    reference_clean = question.correct_answer.replace("cm²", "cm2").replace("m²", "m2")
    if normalize_text(student_clean) == normalize_text(reference_clean):
        return float(question.max_score)

    return 0.0


def score_exam(answers: dict[str, str], questions: tuple[ExamQuestion, ...]) -> float:
    """Return total earned points for a full answer sheet."""
    question_map = {question.question_id: question for question in questions}
    return sum(
        score_answer(question_map[question_id], answer)
        for question_id, answer in answers.items()
        if question_id in question_map
    )


def verdict_from_score(earned: float, max_score: int) -> str:
    """Map earned points to tutor verdict."""
    if earned <= 0:
        return "wrong"
    if earned >= max_score:
        return "correct"
    return "wrong"


def accuracy_percent(earned: float, total: float = 100.0) -> float:
    """Convert earned points to a homepage accuracy percentage."""
    if total <= 0:
        return 0.0
    return round(earned / total * 100, 1)
