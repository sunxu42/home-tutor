"""Tests for the LLM HTTP client."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from home_tutor.services.llm.client import LlmClient, LlmClientError
from home_tutor.services.llm.config import LlmProviderConfig

_PROVIDER = LlmProviderConfig(
    name="mock",
    api_key="sk-test",
    base_url="https://example.com/v1",
    model="mock-model",
)


def _disable_langfuse(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_ENABLED", raising=False)


@pytest.mark.asyncio
async def test_chat_json_skips_langfuse_when_disabled(monkeypatch) -> None:
    _disable_langfuse(monkeypatch)

    client = LlmClient(timeout_sec=5.0)
    body = {
        "choices": [{"message": {"content": '{"verdict":"correct"}'}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
    }

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json() -> dict:
            return body

    with patch("home_tutor.services.llm.client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = FakeResponse()
        mock_client_cls.return_value = mock_client

        parsed = await client.chat_json(
            _PROVIDER,
            system_prompt="system",
            user_prompt="user",
        )

    assert parsed["verdict"] == "correct"


@pytest.mark.asyncio
async def test_chat_json_raises_clear_error_on_timeout(monkeypatch) -> None:
    _disable_langfuse(monkeypatch)

    client = LlmClient(timeout_sec=12.0)

    with patch("home_tutor.services.llm.client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.side_effect = httpx.ReadTimeout("timed out")
        mock_client_cls.return_value = mock_client

        with pytest.raises(LlmClientError, match="LLM 请求超时（12s）"):
            await client.chat_json(
                _PROVIDER,
                system_prompt="system",
                user_prompt="user",
            )

        mock_client_cls.assert_called_once_with(timeout=12.0)
