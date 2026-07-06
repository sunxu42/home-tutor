"""Streaming tutor chat agent."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

from home_tutor.services.llm.client import LlmClient, LlmClientError
from home_tutor.services.llm.config import load_llm_settings
from home_tutor.services.tutor_chat.a2ui_builder import build_a2ui_messages
from home_tutor.services.tutor_chat.context_assembler import assemble_context
from home_tutor.services.tutor_chat.prompts import CHAT_SYSTEM_PROMPT, build_chat_user_prompt


def _payload_from_stream(content: str) -> dict[str, Any]:
    """Parse streamed JSON content into a tutor chat payload."""
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return {"reply_text": content, "paragraphs": [content], "actions": []}
    if not isinstance(parsed, dict):
        return {"reply_text": content, "paragraphs": [content], "actions": []}
    return parsed


def _reply_text_from_payload(payload: dict[str, Any]) -> str:
    reply_text = str(payload.get("reply_text") or payload.get("summary") or "")
    if not reply_text and payload.get("paragraphs"):
        paragraphs = payload.get("paragraphs")
        if isinstance(paragraphs, list) and paragraphs:
            reply_text = str(paragraphs[0])
    return reply_text


async def run_tutor_chat(
    *,
    message: str,
    context: dict[str, Any],
    client: LlmClient | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Run one tutor chat round and yield AG-UI events."""
    llm = client or LlmClient()
    settings = load_llm_settings()
    provider = settings.active()
    if provider is None:
        raise LlmClientError("LLM provider not configured")

    ctx = assemble_context(context)
    yield {"type": "RUN_STARTED"}
    yield {"type": "TEXT_MESSAGE_START", "messageId": "m1", "role": "assistant"}

    accumulated = ""
    async for delta in llm.chat_stream_content(
        provider,
        system_prompt=CHAT_SYSTEM_PROMPT,
        user_prompt=build_chat_user_prompt(ctx.model_dump_json(), message),
    ):
        accumulated += delta
        yield {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": delta}

    yield {"type": "TEXT_MESSAGE_END", "messageId": "m1"}

    payload = _payload_from_stream(accumulated)
    reply_text = _reply_text_from_payload(payload)
    if not reply_text:
        reply_text = accumulated

    a2ui = build_a2ui_messages(surface_id=ctx.a2ui.surface_id, payload=payload)
    yield {"type": "CUSTOM", "name": "a2ui", "value": a2ui}
    yield {"type": "RUN_FINISHED"}
