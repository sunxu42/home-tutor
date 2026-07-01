"""Rich tutor copy templates for mock fixture generation."""

from __future__ import annotations

import re
from typing import Any

from exam_g6_final_2025 import EXAM_QUESTIONS, ExamQuestion
from exam_scoring import normalize_text, score_answer, verdict_from_score

_QUESTION_MAP = {question.question_id: question for question in EXAM_QUESTIONS}

# Known wrong-answer patterns -> error metadata.
_WRONG_PATTERNS: dict[str, list[dict[str, str]]] = {
    "q01": [
        {
            "match": "210",
            "category": "concept_error",
            "subcategory": "fraction_of_quantity",
            "summary": "忘了再乘六分之七",
            "hint": "你算出了大班总人数，但题目要的是中班人数。",
        },
    ],
    "q02": [
        {
            "match": "36",
            "category": "calculation_error",
            "subcategory": "reverse_fraction",
            "summary": "第二空单位量找错",
            "hint": "36kg 比某数多 1/2，这个某数要比 36 小。",
        },
    ],
    "q03": [
        {
            "match": "45",
            "category": "concept_error",
            "subcategory": "angle_ratio",
            "summary": "角度比理解反了",
            "hint": "顶角和底角比是 1:2，说明底角更大。",
        },
    ],
    "q06": [
        {
            "match": "21",
            "category": "concept_error",
            "subcategory": "sequence_pattern",
            "summary": "规律数错了",
            "hint": "再数一数每层新增的小正方形。",
        },
    ],
    "q17": [
        {
            "match": "A",
            "category": "concept_error",
            "subcategory": "percent_change",
            "summary": "提价降价不能抵消",
            "hint": "先涨 20% 再降 20%，基数已经变了。",
        },
    ],
    "q20": [
        {
            "match": "3.3",
            "category": "calculation_error",
            "subcategory": "mixed_number",
            "summary": "第①题计算有误",
            "hint": "带分数和乘法要一步步算，别急。",
        },
        {
            "match": "3/16",
            "category": "calculation_error",
            "subcategory": "fraction_ops",
            "summary": "第④题分数运算粗心",
            "hint": "最后一步通分再检查一下。",
        },
    ],
    "q28": [
        {
            "match": "7.54",
            "category": "calculation_error",
            "subcategory": "track_offset",
            "summary": "起跑线前移距离算偏了",
            "hint": "第三问要和跑道宽、π 联系起来。",
        },
        {
            "match": "7.5",
            "category": "calculation_error",
            "subcategory": "track_offset",
            "summary": "起跑线前移距离近似了",
            "hint": "结果要保留足够有效数字。",
        },
    ],
    "q30": [
        {
            "match": "D34",
            "category": "calculation_error",
            "subcategory": "percentage_table",
            "summary": "统计图百分比差了一点",
            "hint": "先求总人数，再反推各项百分比。",
        },
        {
            "match": "300",
            "category": "concept_error",
            "subcategory": "percentage_table",
            "summary": "总人数估错了",
            "hint": "把已知百分数和件数对应起来列方程。",
        },
    ],
}


def _match_pattern(question_id: str, student_answer: str) -> dict[str, str] | None:
    for pattern in _WRONG_PATTERNS.get(question_id, []):
        if pattern["match"] in student_answer:
            return pattern
    return None


def _process_comment(package: dict[str, Any], *, stuck: bool) -> str:
    metrics = package.get("process_metrics", {})
    active_ms = int(metrics.get("active_duration_ms", 0))
    revisions = int(metrics.get("revision_count", 0))
    minutes = max(1, active_ms // 60_000)

    if stuck:
        return f"这道题你写了大约 {minutes} 分钟，中间停笔较久，说明在认真想。"
    if revisions > 0:
        return "你中途改过一次答案，最后坚持写完了，这个习惯很好。"
    if active_ms < 90_000:
        return "写得比较快，说明这类题你已经比较熟练。"
    return "书写节奏平稳，步骤比较清楚。"


def build_tutor_content(
    *,
    session_id: str,
    question_id: str,
    package: dict[str, Any],
) -> dict[str, Any]:
    """Build a ready TutorContent document from a question package."""
    question = _QUESTION_MAP[question_id]
    student = package.get("final_answer", {}).get("text", "")
    reference = question.correct_answer
    earned = score_answer(question, student)
    verdict = verdict_from_score(earned, question.max_score)
    number = package.get("number", 0)
    stuck = bool(package.get("process_metrics", {}).get("stuck"))

    if verdict == "correct":
        summary = "这题完成得很好！"
        paragraphs = [
            f"第 {number} 题你的答案是正确的。",
            "关键步骤都想到了，继续保持。",
        ]
        error_classification = {"category": "correct"}
    else:
        pattern = _match_pattern(question_id, student)
        if pattern:
            summary = pattern["summary"]
            paragraphs = [
                f"第 {number} 题你的答案是：{student or '（未作答）'}。",
                pattern["hint"],
                f"正确答案是：{reference}。",
            ]
            error_classification = {
                "category": pattern["category"],
                "subcategory": pattern["subcategory"],
                "confidence": 0.88,
            }
        else:
            summary = "这题还有提升空间"
            paragraphs = [
                f"第 {number} 题你的答案是：{student or '（未作答）'}。",
                f"正确答案是：{reference}。",
                "回忆一下本题用到的知识点，再练一道类似的。",
            ]
            error_classification = {
                "category": "unknown",
                "confidence": 0.6,
            }

    if not student.strip():
        summary = "这题还没写完"
        paragraphs = [
            f"第 {number} 题暂时没识别到完整答案。",
            f"参考答案是：{reference}。",
            "下次可以留一点时间检查有没有漏写。",
        ]
        error_classification = {"category": "incomplete", "confidence": 0.9}
        verdict = "unknown"

    return {
        "schema_version": "home-tutor.tutor-content.v1",
        "session_id": session_id,
        "question_id": question_id,
        "analysis_status": "ready",
        "verdict": verdict,
        "reference_answer": reference,
        "summary": summary,
        "explanation_paragraphs": paragraphs,
        "error_classification": error_classification,
        "process_comment": _process_comment(package, stuck=stuck),
        "actions": [{"id": "explain_more", "label": "详细讲讲", "enabled": False}],
        "stale": False,
        "generated_at": package.get("updated_at", "2026-06-22T15:00:00.000Z"),
        "model": "mock-v2",
        "error": None,
    }
