"""Build A2UI v0.9 messages from tutor chat LLM JSON."""

from __future__ import annotations

from typing import Any


def build_a2ui_messages(
    *,
    surface_id: str,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Convert chat response JSON into A2UI message list."""
    components: list[dict[str, Any]] = []
    counter = 0

    def next_id(prefix: str) -> str:
        nonlocal counter
        counter += 1
        return f"{prefix}-{counter}"

    for paragraph in payload.get("paragraphs") or []:
        components.append({
            "id": next_id("text"),
            "component": "TutorText",
            "text": str(paragraph),
        })

    compare = payload.get("answer_compare")
    if isinstance(compare, dict):
        components.append({
            "id": next_id("compare"),
            "component": "AnswerCompare",
            "student": str(compare.get("student", "")),
            "reference": str(compare.get("reference", "")),
        })

    for step in payload.get("process_steps") or []:
        if not isinstance(step, dict):
            continue
        components.append({
            "id": next_id("step"),
            "component": "ProcessStep",
            "title": str(step.get("title", "")),
            "text": str(step.get("text", "")),
            "expanded": bool(step.get("expanded", False)),
        })

    hints = payload.get("hints")
    if isinstance(hints, list) and hints:
        components.append({
            "id": next_id("hints"),
            "component": "HintLadder",
            "items": [str(item) for item in hints],
        })

    for frame in payload.get("key_frames") or []:
        if not isinstance(frame, dict):
            continue
        components.append({
            "id": next_id("frame"),
            "component": "KeyFrameThumb",
            "frameId": str(frame.get("frameId", frame.get("frame_id", ""))),
            "imageUrl": str(frame.get("imageUrl", frame.get("image_url", ""))),
            "label": str(frame.get("label", "")),
        })

    for action in payload.get("actions") or []:
        components.append({
            "id": next_id("action"),
            "component": "ActionChip",
            "actionId": str(action.get("id", "")),
            "label": str(action.get("label", "")),
        })

    return [
        {
            "version": "0.9",
            "createSurface": {"surfaceId": surface_id, "catalogId": "home-tutor"},
        },
        {
            "version": "0.9",
            "updateComponents": {"surfaceId": surface_id, "components": components},
        },
        {
            "version": "0.9",
            "updateDataModel": {
                "surfaceId": surface_id,
                "path": "/",
                "value": payload.get("data_model_patch") or {},
            },
        },
    ]
