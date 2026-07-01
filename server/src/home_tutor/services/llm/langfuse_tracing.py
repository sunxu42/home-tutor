"""Langfuse observability helpers for tutor LLM calls."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from home_tutor.core.logging import get_logger, log_trace

logger = get_logger(__name__)

_ENV_LOADED = False


@dataclass(frozen=True)
class LangfuseSettings:
    """Resolved Langfuse configuration."""

    enabled: bool
    public_key: str
    secret_key: str
    host: str


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def ensure_langfuse_env_loaded() -> None:
    """Load .env so LANGFUSE_* variables are visible to the SDK."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    load_dotenv(Path(".env"), override=False)
    _ENV_LOADED = True


def load_langfuse_settings() -> LangfuseSettings:
    """Parse Langfuse settings from environment variables."""
    ensure_langfuse_env_loaded()
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "").strip()
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "").strip()
    host = (
        os.environ.get("LANGFUSE_BASE_URL")
        or os.environ.get("LANGFUSE_HOST")
        or "https://cloud.langfuse.com"
    ).strip().rstrip("/")
    has_keys = bool(public_key and secret_key)
    enabled = _env_bool("LANGFUSE_ENABLED", has_keys) and has_keys
    return LangfuseSettings(
        enabled=enabled,
        public_key=public_key,
        secret_key=secret_key,
        host=host,
    )


def is_tracing_enabled() -> bool:
    """Return True when Langfuse tracing should be active."""
    return load_langfuse_settings().enabled


def init_langfuse() -> None:
    """Warm up the Langfuse client after environment variables are loaded."""
    ensure_langfuse_env_loaded()
    settings = load_langfuse_settings()
    if not settings.enabled:
        log_trace(logger, "LANGFUSE_DISABLED")
        return

    from langfuse import get_client

    get_client()
    log_trace(logger, "LANGFUSE_ENABLED", host=settings.host)


def flush_langfuse() -> None:
    """Flush pending Langfuse events; safe to call when tracing is disabled."""
    ensure_langfuse_env_loaded()
    if not load_langfuse_settings().enabled:
        return

    from langfuse import get_client

    try:
        get_client().flush()
    except Exception:
        logger.exception("langfuse_flush_failed")


def map_openai_usage(body: dict[str, Any]) -> dict[str, int] | None:
    """Map OpenAI-compatible usage fields to Langfuse usage_details."""
    usage = body.get("usage")
    if not isinstance(usage, dict):
        return None

    details: dict[str, int] = {}
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    total_tokens = usage.get("total_tokens")
    if isinstance(prompt_tokens, int):
        details["input"] = prompt_tokens
    if isinstance(completion_tokens, int):
        details["output"] = completion_tokens
    if isinstance(total_tokens, int):
        details["total"] = total_tokens
    return details or None
