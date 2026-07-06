"""HMAC WebSocket tokens for the speech gateway."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from home_tutor.core.config import settings

_DEFAULT_TTL_SEC = 3600
_DEV_WS_SECRET = "dev-speech-ws-secret"


def resolve_ws_secret() -> str:
    """Return configured speech WS secret, with a debug-only fallback."""
    secret = settings.speech_ws_secret.strip()
    if secret:
        return secret
    if settings.debug:
        return _DEV_WS_SECRET
    return ""


def create_ws_token(*, ttl_sec: int = _DEFAULT_TTL_SEC) -> dict[str, Any]:
    """Create a signed WebSocket access token."""
    secret = resolve_ws_secret()
    if not secret:
        raise ValueError("SPEECH_WS_SECRET not configured")

    expires_at = int(time.time()) + ttl_sec
    payload = {"exp": expires_at}
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = hmac.new(secret.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return {"token": f"{payload_b64}.{signature}", "expiresAt": expires_at}


def validate_ws_token(token: str) -> bool:
    """Validate a WebSocket access token signature and expiry."""
    secret = resolve_ws_secret()
    if not secret or not token:
        return False

    try:
        payload_b64, signature = token.rsplit(".", 1)
        expected = hmac.new(secret.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return False

        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        exp = payload.get("exp")
        return isinstance(exp, int) and exp >= time.time()
    except (ValueError, json.JSONDecodeError, TypeError):
        return False
