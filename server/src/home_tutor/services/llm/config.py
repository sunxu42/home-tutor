"""LLM provider configuration."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from home_tutor.core.config import settings

_PROVIDER_ENV = re.compile(r"^LLM_PROVIDER_([A-Z0-9_]+)_(API_KEY|BASE_URL|MODEL)$")


@dataclass(frozen=True)
class LlmProviderConfig:
    """Connection settings for one named LLM provider."""

    name: str
    api_key: str
    base_url: str
    model: str


@dataclass(frozen=True)
class LlmSettings:
    """Resolved LLM runtime settings."""

    active_provider: str
    save_token_mode: bool
    skip_fixture_tutor: bool
    request_timeout_sec: float
    providers: dict[str, LlmProviderConfig]

    def active(self) -> LlmProviderConfig | None:
        """Return the configured active provider, if any."""
        if not self.active_provider:
            return None
        return self.providers.get(self.active_provider.lower())

    def is_configured(self) -> bool:
        """True when an active provider has API key and model."""
        provider = self.active()
        if provider is None:
            return False
        return bool(provider.api_key.strip() and provider.model.strip())


def _provider_key_from_env(name: str) -> str:
    return name.lower().replace("__", "_")


def load_llm_settings() -> LlmSettings:
    """Parse named LLM providers from environment variables."""
    # Pydantic Settings reads .env for its own fields only; provider keys use LLM_PROVIDER_*.
    load_dotenv(Path(".env"), override=False)

    buckets: dict[str, dict[str, str]] = {}
    for key, value in os.environ.items():
        match = _PROVIDER_ENV.match(key)
        if not match:
            continue
        raw_name, field = match.group(1), match.group(2).lower()
        provider_name = _provider_key_from_env(raw_name)
        buckets.setdefault(provider_name, {})[field] = value

    providers: dict[str, LlmProviderConfig] = {}
    for name, fields in buckets.items():
        api_key = fields.get("api_key", "")
        base_url = fields.get("base_url", "")
        model = fields.get("model", "")
        if not api_key and not base_url and not model:
            continue
        providers[name] = LlmProviderConfig(
            name=name,
            api_key=api_key,
            base_url=base_url.rstrip("/"),
            model=model,
        )

    def _env_bool(name: str, default: bool) -> bool:
        raw = os.environ.get(name)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    active = os.environ.get("LLM_ACTIVE_PROVIDER", settings.llm_active_provider)
    return LlmSettings(
        active_provider=active.lower().strip(),
        save_token_mode=_env_bool("LLM_SAVE_TOKEN_MODE", settings.llm_save_token_mode),
        skip_fixture_tutor=_env_bool("LLM_SKIP_FIXTURE_TUTOR", settings.llm_skip_fixture_tutor),
        request_timeout_sec=float(
            os.environ.get("LLM_REQUEST_TIMEOUT_SEC", settings.llm_request_timeout_sec)
        ),
        providers=providers,
    )
