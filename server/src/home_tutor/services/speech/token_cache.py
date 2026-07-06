"""TTL cache for Alibaba NLS tokens."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

_NLS_TOKEN_TTL_SEC = 23 * 3600


@dataclass
class _CacheEntry:
    token: str
    expires_at: float


_cache: _CacheEntry | None = None


async def get_or_create_token(
    factory: Callable[[], Awaitable[str]],
    *,
    ttl_sec: float = _NLS_TOKEN_TTL_SEC,
) -> str:
    """Return a cached NLS token or fetch a new one via ``factory``."""
    global _cache
    now = time.time()
    if _cache is not None and _cache.expires_at > now:
        return _cache.token

    token = await factory()
    _cache = _CacheEntry(token=token, expires_at=now + ttl_sec)
    return token


def clear_token_cache() -> None:
    """Clear the in-memory NLS token cache (for tests)."""
    global _cache
    _cache = None
