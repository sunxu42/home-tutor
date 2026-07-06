"""LangGraph tutor agent for CopilotKit / AG-UI.

Single-node graph (START → tutor_chat → END) bridges CopilotKit to our AG-UI
event stream. When multi-step planning is needed, add nodes here rather than
introducing a parallel agent path.
"""

from __future__ import annotations

from typing import Any

from copilotkit import LangGraphAGUIAgent
from copilotkit.langgraph import CopilotKitState, copilotkit_emit_message, copilotkit_emit_state
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from home_tutor.services.tutor_chat.chat_agent import run_tutor_chat
from home_tutor.services.tutor_chat.context_helpers import extract_tutor_context, extract_user_message


class TutorGraphState(CopilotKitState):
    """CopilotKit state extended with explicit tutor context."""

    tutor_session_context: dict[str, Any]
    a2ui_messages: list[dict[str, Any]]
    a2ui_data_model: dict[str, Any]


def _extract_a2ui_data_model(messages: list[dict[str, Any]]) -> dict[str, Any]:
    for message in messages:
        update = message.get("updateDataModel")
        if not isinstance(update, dict):
            continue
        value = update.get("value")
        if isinstance(value, dict):
            return value
    return {}


async def tutor_chat_node(state: TutorGraphState, config: RunnableConfig) -> dict[str, Any]:
    """Run one tutor chat round and emit CopilotKit messages + A2UI state."""
    user_message = extract_user_message(state)
    if not user_message.strip():
        return {"messages": [AIMessage(content="")]}

    context = extract_tutor_context(state)
    if not context:
        reply = "暂时无法获取题目上下文，请刷新页面后重试。"
        await copilotkit_emit_message(config, message=reply)
        return {"messages": [AIMessage(content=reply)]}

    reply_text = ""
    a2ui_messages: list[dict[str, Any]] = []
    a2ui_data_model: dict[str, Any] = {}

    async for event in run_tutor_chat(message=user_message, context=context):
        event_type = event.get("type")
        if event_type == "TEXT_MESSAGE_CONTENT":
            reply_text += str(event.get("delta") or "")
        elif event_type == "CUSTOM" and event.get("name") == "a2ui":
            value = event.get("value")
            if isinstance(value, list):
                a2ui_messages = value
                a2ui_data_model = _extract_a2ui_data_model(value)

    if reply_text:
        await copilotkit_emit_message(config, message=reply_text)

    if a2ui_messages:
        await copilotkit_emit_state(
            config,
            {
                "a2ui_messages": a2ui_messages,
                "a2ui_data_model": a2ui_data_model,
            },
        )

    return {
        "messages": [AIMessage(content=reply_text)],
        "a2ui_messages": a2ui_messages,
        "a2ui_data_model": a2ui_data_model,
    }


def build_tutor_graph():
    """Compile the single-node tutor LangGraph."""
    graph = StateGraph(TutorGraphState)
    graph.add_node("tutor_chat", tutor_chat_node)
    graph.add_edge(START, "tutor_chat")
    graph.add_edge("tutor_chat", END)
    return graph.compile()


def build_tutor_agent() -> LangGraphAGUIAgent:
    """Create the CopilotKit AG-UI agent for session review tutoring."""
    return LangGraphAGUIAgent(
        name="tutor",
        description="Interactive tutor for Home Tutor session review.",
        graph=build_tutor_graph(),
    )
