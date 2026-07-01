"""Tests for Langfuse tracing helpers."""

from home_tutor.services.llm.langfuse_tracing import (
    load_langfuse_settings,
    map_openai_usage,
)


def test_load_langfuse_settings_disabled_without_keys(monkeypatch) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_ENABLED", raising=False)

    settings = load_langfuse_settings()
    assert settings.enabled is False


def test_load_langfuse_settings_enabled_with_keys(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.delenv("LANGFUSE_ENABLED", raising=False)

    settings = load_langfuse_settings()
    assert settings.enabled is True
    assert settings.public_key == "pk-test"


def test_map_openai_usage() -> None:
    usage = map_openai_usage(
        {
            "usage": {
                "prompt_tokens": 12,
                "completion_tokens": 34,
                "total_tokens": 46,
            }
        }
    )
    assert usage == {"input": 12, "output": 34, "total": 46}


def test_map_openai_usage_missing() -> None:
    assert map_openai_usage({}) is None
