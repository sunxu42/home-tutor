"""Tests for session materializer."""

from home_tutor.services.analysis.materializer import (
    build_question_package,
    build_timeline_index,
)


def test_build_timeline_index_from_focus_blur() -> None:
    events = [
        {"type": "question.focus", "t_offset_ms": 1000, "question_id": "q01"},
        {"type": "question.blur", "t_offset_ms": 5000, "question_id": "q01"},
        {"type": "session.end", "t_offset_ms": 10000},
    ]
    question_numbers = {"q01": 1}
    verdicts = {"q01": "wrong"}

    index = build_timeline_index(
        session_id="a1000001-0001-4001-8001-000000000001",
        events=events,
        question_numbers=question_numbers,
        verdicts=verdicts,
    )

    assert index["duration_ms"] == 10000
    assert len(index["segments"]) == 1
    assert index["segments"][0] == {
        "question_id": "q01",
        "number": 1,
        "start_ms": 1000,
        "end_ms": 5000,
        "verdict": "wrong",
    }


def test_build_question_package_mcq_options() -> None:
    pkg = build_question_package(
        session_id="a1000001-0001-4001-8001-000000000001",
        question={
            "question_id": "q12",
            "page_id": "page_1",
            "index_on_page": 12,
            "number": 12,
            "prompt_text": "示例选择题",
            "question_type": "multiple_choice",
            "options": [
                {"key": "A", "text": "选项甲"},
                {"key": "B", "text": "选项乙"},
            ],
        },
        regions=[],
        events=[],
    )
    assert pkg["question_type"] == "multiple_choice"
    assert pkg["prompt"]["options"][0]["key"] == "A"


def test_build_question_package_answer_timeline() -> None:
    events = [
        {"type": "question.focus", "t_offset_ms": 1000, "question_id": "q01"},
        {
            "type": "answer.appeared",
            "t_offset_ms": 2000,
            "question_id": "q01",
            "region_id": "r_answer_q01",
            "payload": {"text": "210", "confidence": 0.9},
        },
        {
            "type": "answer.changed",
            "t_offset_ms": 3000,
            "question_id": "q01",
            "region_id": "r_answer_q01",
            "payload": {"text": "180", "prev_text": "210", "confidence": 0.92},
        },
        {"type": "question.blur", "t_offset_ms": 5000, "question_id": "q01"},
    ]

    pkg = build_question_package(
        session_id="a1000001-0001-4001-8001-000000000001",
        question={
            "question_id": "q01",
            "page_id": "page_1",
            "index_on_page": 1,
            "number": 1,
            "prompt_text": "中班有多少人？",
            "question_type": "fill_blank",
        },
        regions=[
            {
                "region_id": "r_answer_q01",
                "question_id": "q01",
                "role": "student_answer",
                "bbox": {"x": 0.1, "y": 0.2, "w": 0.1, "h": 0.05},
            }
        ],
        events=events,
    )

    assert pkg["final_answer"]["text"] == "180"
    assert len(pkg["answer_timeline"]) == 2
    assert pkg["answer_timeline"][0]["kind"] == "appeared"
    assert pkg["answer_timeline"][1]["prev_text"] == "210"
    assert pkg["focus_segments"][0]["duration_ms"] == 4000
