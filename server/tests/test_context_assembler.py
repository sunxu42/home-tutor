"""Tests for tutor session context assembly."""

from home_tutor.models.tutor_session_context import TutorSessionContext
from home_tutor.services.tutor_chat.context_assembler import assemble_context, trim_transcript


def test_tutor_session_context_schema_version() -> None:
    ctx = TutorSessionContext(
        page="session_review",
        session_id="score62",
        question_id="q01",
        navigation={"question_index": 1, "total_questions": 10},
        package={
            "prompt_text": "1+1=?",
            "final_answer": "3",
            "verdict": "wrong",
        },
        tutor={
            "summary": "算错了",
            "explanation_paragraphs": ["再想想"],
            "analysis_status": "ready",
        },
        a2ui={
            "surface_id": "tutor-panel",
            "data_model": {},
            "recent_actions": [],
        },
        transcript=[],
    )
    assert ctx.schema_version == "home-tutor.tutor-session-context.v1"


def test_trim_transcript_keeps_last_ten() -> None:
    entries = [
        {"role": "user", "content": f"m{i}", "source": "text", "ts": i}
        for i in range(15)
    ]
    trimmed = trim_transcript(entries, max_entries=10)
    assert len(trimmed) == 10
    assert trimmed[0]["content"] == "m5"


def test_assemble_context_enriches_process_summary() -> None:
    ctx = assemble_context(
        {
            "page": "session_review",
            "session_id": "score62",
            "question_id": "q01",
            "navigation": {"question_index": 1, "total_questions": 5},
            "package": {
                "prompt_text": "1+1",
                "final_answer": "2",
                "verdict": "correct",
                "process_metrics": {
                    "active_duration_ms": 5000,
                    "revision_count": 2,
                },
            },
            "tutor": {
                "summary": "对了",
                "explanation_paragraphs": ["很好"],
                "analysis_status": "ready",
            },
            "a2ui": {
                "surface_id": "tutor-panel",
                "data_model": {},
                "recent_actions": [],
            },
            "transcript": [],
        },
    )
    assert ctx.package.process_summary == "用时约5秒，修改2次"
