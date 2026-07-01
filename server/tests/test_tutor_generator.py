"""Tests for tutor payload normalization."""

from home_tutor.services.llm.tutor_generator import normalize_llm_payload


def test_normalize_llm_payload_maps_fields() -> None:
    tutor = normalize_llm_payload(
        session_id="sess-1",
        question_id="q01",
        model="test-model",
        payload={
            "verdict": "wrong",
            "reference_answer": "20",
            "summary": "进位错了",
            "explanation_paragraphs": ["第一段", "第二段"],
            "process_comment": "你改了两次答案。",
            "error_classification": {
                "category": "calculation_error",
                "subcategory": "carry_mistake",
                "confidence": 0.9,
            },
        },
    )
    assert tutor["analysis_status"] == "ready"
    assert tutor["verdict"] == "wrong"
    assert tutor["process_comment"] == "你改了两次答案。"
    assert tutor["error_classification"]["category"] == "calculation_error"
    assert tutor["model"] == "test-model"
