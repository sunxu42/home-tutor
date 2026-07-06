"""Tests for CopilotKit tutor LangGraph."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from langchain_core.messages import HumanMessage

from home_tutor.services.tutor_chat import copilot_graph


def _sample_context() -> dict[str, Any]:
    return {
        "page": "session_review",
        "session_id": "score62",
        "question_id": "q01",
        "navigation": {"question_index": 1, "total_questions": 5},
        "package": {
            "prompt_text": "1+1",
            "final_answer": "2",
            "verdict": "correct",
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
    }


async def _fake_run_tutor_chat(
    *,
    message: str,
    context: dict[str, Any],
    client: Any = None,
) -> AsyncIterator[dict[str, Any]]:
    _ = message, context, client
    yield {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": "你好"}
    yield {
        "type": "CUSTOM",
        "name": "a2ui",
        "value": [
            {
                "version": "0.9",
                "createSurface": {"surfaceId": "tutor-panel", "catalogId": "home-tutor"},
            },
            {
                "version": "0.9",
                "updateComponents": {"surfaceId": "tutor-panel", "components": []},
            },
            {
                "version": "0.9",
                "updateDataModel": {
                    "surfaceId": "tutor-panel",
                    "path": "/",
                    "value": {"step": 1},
                },
            },
        ],
    }


@pytest.mark.asyncio
async def test_tutor_chat_node_emits_a2ui_state(monkeypatch: pytest.MonkeyPatch) -> None:
    emitted_states: list[dict[str, Any]] = []
    emitted_messages: list[str] = []

    async def fake_emit_state(_config: object, state: dict[str, Any]) -> bool:
        emitted_states.append(state)
        return True

    async def fake_emit_message(_config: object, message: str) -> bool:
        emitted_messages.append(message)
        return True

    monkeypatch.setattr(copilot_graph, "run_tutor_chat", _fake_run_tutor_chat)
    monkeypatch.setattr(copilot_graph, "copilotkit_emit_state", fake_emit_state)
    monkeypatch.setattr(copilot_graph, "copilotkit_emit_message", fake_emit_message)

    state = {
        "messages": [HumanMessage(content="讲一讲")],
        "tutor_session_context": _sample_context(),
        "a2ui_messages": [],
        "a2ui_data_model": {},
    }

    result = await copilot_graph.tutor_chat_node(state, config={})

    assert emitted_messages == ["你好"]
    assert emitted_states[0]["a2ui_messages"]
    assert emitted_states[0]["a2ui_data_model"] == {"step": 1}
    assert result["a2ui_data_model"] == {"step": 1}
    assert result["messages"][0].content == "你好"
