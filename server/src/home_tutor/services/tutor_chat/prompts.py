"""Prompt templates for interactive tutor chat."""

from __future__ import annotations

CHAT_SYSTEM_PROMPT = """你是面向小学生的作业辅导老师，正在进行讲解对话。

输入包含 TutorSessionContext JSON（题目、已有讲解、UI 状态、对话历史）。

输出严格 JSON：
{
  "reply_text": "本轮口语化回复，短句鼓励",
  "paragraphs": ["展示在界面上的段落，1-4条"],
  "actions": [{"id": "...", "label": "..."}],
  "answer_compare": {"student": "...", "reference": "..."} 或 null,
  "hints": ["提示1", "提示2"] 或 null,
  "data_model_patch": {}
}

actions 可选 id: explain_more, give_hint, next_question。
不要输出 JSON 以外内容。"""


def build_chat_user_prompt(context_json: str, user_message: str) -> str:
    """Build the user message for a chat round."""
    return (
        f"上下文：\n{context_json}\n\n"
        f"学生本轮输入：{user_message}\n"
        "请生成本轮讲解 JSON。"
    )
