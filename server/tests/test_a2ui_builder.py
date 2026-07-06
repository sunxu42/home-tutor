"""Tests for A2UI message builder."""

from home_tutor.services.tutor_chat.a2ui_builder import build_a2ui_messages


def test_build_surface_from_chat_response() -> None:
    messages = build_a2ui_messages(
        surface_id="tutor-panel",
        payload={
            "reply_text": "我们来看进位这一步。",
            "paragraphs": ["第一句", "第二句"],
            "actions": [{"id": "explain_more", "label": "详细讲讲"}],
            "answer_compare": {
                "student": "19",
                "reference": "20",
            },
        },
    )
    assert messages[0]["version"] == "0.9"
    assert any("createSurface" in message for message in messages)
    components = messages[1]["updateComponents"]["components"]
    assert any(c["component"] == "TutorText" for c in components)
    assert any(c["component"] == "ActionChip" for c in components)


def test_build_process_steps_and_key_frames() -> None:
    messages = build_a2ui_messages(
        surface_id="tutor-panel",
        payload={
            "paragraphs": ["讲解"],
            "process_steps": [{"title": "第一步", "text": "列竖式", "expanded": True}],
            "key_frames": [{"frameId": "f1", "imageUrl": "https://example.test/f1.jpg", "label": "板书"}],
        },
    )
    components = messages[1]["updateComponents"]["components"]
    assert any(c["component"] == "ProcessStep" for c in components)
    assert any(c["component"] == "KeyFrameThumb" for c in components)
