"""OpenAI-compatible async HTTP client for chat completions."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from home_tutor.core.config import settings
from home_tutor.core.logging import get_logger, log_milestone, log_trace
from home_tutor.services.llm.config import LlmProviderConfig
from home_tutor.services.llm.langfuse_tracing import is_tracing_enabled, map_openai_usage

logger = get_logger(__name__)


class LlmClientError(Exception):
    """Raised when the LLM HTTP API returns an error."""


class LlmClient:
    """Minimal OpenAI-compatible chat completions client."""

    def __init__(self, *, timeout_sec: float = 30.0) -> None:
        self._timeout = timeout_sec

    async def chat_json(
        self,
        provider: LlmProviderConfig,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """Request a JSON object response from the chat completions API."""
        url = f"{provider.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        }
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        payload = {
            "model": provider.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        if is_tracing_enabled():
            return await self._chat_json_traced(
                provider=provider,
                url=url,
                headers=headers,
                payload=payload,
                messages=messages,
            )
        return await self._chat_json_request(url=url, headers=headers, payload=payload)

    async def _chat_json_traced(
        self,
        *,
        provider: LlmProviderConfig,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        messages: list[dict[str, str]],
    ) -> dict[str, Any]:
        from langfuse import get_client

        langfuse = get_client()
        with langfuse.start_as_current_observation(
            as_type="generation",
            name="tutor-chat-completion",
            model=provider.model,
            input=messages,
            metadata={
                "provider": provider.name,
                "base_url": provider.base_url,
            },
            model_parameters={
                "temperature": payload["temperature"],
                "response_format": payload["response_format"]["type"],
            },
        ) as generation:
            try:
                parsed, body, content = await self._chat_json_request_with_raw(
                    url=url,
                    headers=headers,
                    payload=payload,
                )
            except LlmClientError as exc:
                generation.update(level="ERROR", status_message=str(exc))
                raise

            generation.update(
                output=content,
                usage_details=map_openai_usage(body),
            )
            return parsed

    async def _chat_json_request(
        self,
        *,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        parsed, _, _ = await self._chat_json_request_with_raw(
            url=url,
            headers=headers,
            payload=payload,
        )
        return parsed

    async def _chat_json_request_with_raw(
        self,
        *,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any], str]:
        messages = payload.get("messages", [])
        system_prompt = messages[0].get("content", "") if len(messages) >= 1 else ""
        user_prompt = messages[1].get("content", "") if len(messages) >= 2 else ""

        log_milestone(logger, "LLM_REQUEST", model=payload.get("model"))
        if settings.log_mode in {"verbose", "debug"}:
            combined = f"[system] {system_prompt}\n[user] {user_prompt}"
            log_trace(logger, "LLM_PROMPT", prompt_preview=combined)
        start = time.perf_counter()

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
            except httpx.TimeoutException as exc:
                raise LlmClientError(
                    f"LLM 请求超时（{self._timeout:g}s），请稍后重试或增大 LLM_REQUEST_TIMEOUT_SEC"
                ) from exc
            except httpx.HTTPError as exc:
                raise LlmClientError(f"LLM 请求失败：{exc}") from exc

        if response.status_code >= 400:
            logger.warning(
                "LLM_HTTP_ERROR",
                status_code=response.status_code,
                body_preview=response.text[:500],
            )
            raise LlmClientError(f"LLM request failed with status {response.status_code}")

        body = response.json()
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmClientError("LLM response missing message content") from exc

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LlmClientError("LLM response is not valid JSON") from exc

        if not isinstance(parsed, dict):
            raise LlmClientError("LLM JSON response must be an object")

        duration_ms = int((time.perf_counter() - start) * 1000)
        usage = body.get("usage", {})
        milestone_kwargs: dict[str, Any] = {
            "duration_ms": duration_ms,
            "tokens_in": usage.get("prompt_tokens"),
            "tokens_out": usage.get("completion_tokens"),
        }
        if settings.log_llm_verbose:
            milestone_kwargs["response_json"] = content
        log_milestone(logger, "LLM_RESPONSE", **milestone_kwargs)
        if settings.log_mode in {"verbose", "debug"}:
            log_trace(
                logger,
                "LLM_RESPONSE_BODY",
                verdict=parsed.get("verdict"),
                summary=parsed.get("summary"),
            )
        return parsed, body, content
