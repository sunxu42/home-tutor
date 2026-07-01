"""Tests for LLM configuration parsing."""

import os

from home_tutor.services.llm.config import load_llm_settings


def test_load_llm_settings_parses_named_providers(monkeypatch) -> None:
    monkeypatch.setenv("LLM_ACTIVE_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_SAVE_TOKEN_MODE", "true")
    monkeypatch.setenv("LLM_PROVIDER_DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_PROVIDER_DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1/")
    monkeypatch.setenv("LLM_PROVIDER_DEEPSEEK_MODEL", "deepseek-chat")
    monkeypatch.setenv("LLM_PROVIDER_OPENAI_API_KEY", "sk-openai")
    monkeypatch.setenv("LLM_PROVIDER_OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("LLM_PROVIDER_OPENAI_MODEL", "gpt-4o-mini")

    settings = load_llm_settings()
    assert settings.active_provider == "deepseek"
    assert settings.save_token_mode is True
    assert settings.is_configured() is True

    active = settings.active()
    assert active is not None
    assert active.api_key == "sk-test"
    assert active.base_url == "https://api.deepseek.com/v1"
    assert active.model == "deepseek-chat"
    assert "openai" in settings.providers


def test_load_llm_settings_not_configured_without_key(monkeypatch) -> None:
    for key in list(os.environ):
        if key.startswith("LLM_PROVIDER_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("LLM_ACTIVE_PROVIDER", "deepseek")
    monkeypatch.delenv("LLM_PROVIDER_DEEPSEEK_API_KEY", raising=False)

    settings = load_llm_settings()
    assert settings.is_configured() is False


def test_load_llm_settings_reads_provider_keys_from_dotenv(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "LLM_ACTIVE_PROVIDER=glm",
                "LLM_PROVIDER_GLM_API_KEY=sk-from-dotenv",
                "LLM_PROVIDER_GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4",
                "LLM_PROVIDER_GLM_MODEL=glm-4-flash",
            ]
        ),
        encoding="utf-8",
    )
    for key in list(os.environ):
        if key.startswith("LLM_PROVIDER_") or key == "LLM_ACTIVE_PROVIDER":
            monkeypatch.delenv(key, raising=False)

    settings = load_llm_settings()
    assert settings.active_provider == "glm"
    assert settings.is_configured() is True
    active = settings.active()
    assert active is not None
    assert active.api_key == "sk-from-dotenv"
    assert active.base_url == "https://open.bigmodel.cn/api/paas/v4"
    assert active.model == "glm-4-flash"
