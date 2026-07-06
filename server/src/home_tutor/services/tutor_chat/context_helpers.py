"""Helpers for extracting tutor chat inputs from CopilotKit LangGraph state."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage

from copilotkit.langgraph import CopilotKitState


def extract_user_message(state: CopilotKitState) -> str:
    """Return the latest human message content from graph state."""
    for message in reversed(state.get("messages") or []):
        if isinstance(message, HumanMessage):
            content = message.content
            if isinstance(content, str):
                return content
            return str(content)
    return ""


def extract_tutor_context(state: CopilotKitState) -> dict[str, Any]:
    """Resolve tutor session context from graph state or CopilotKit readable."""
    explicit = state.get("tutor_session_context")
    if isinstance(explicit, dict) and explicit:
        return explicit

    copilotkit = state.get("copilotkit") or {}
    for item in copilotkit.get("context") or []:
        if not isinstance(item, dict):
            continue
        if item.get("description") == "tutor_session_context":
            value = item.get("value")
            if isinstance(value, dict):
                return value
    return {}
