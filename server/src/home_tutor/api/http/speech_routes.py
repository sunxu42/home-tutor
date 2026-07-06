"""Speech HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from home_tutor.services.speech.settings import resolve_speech_settings
from home_tutor.services.speech.ws_token import create_ws_token, resolve_ws_secret

router = APIRouter(prefix="/speech", tags=["speech"])


@router.get("/ws-token")
async def get_ws_token() -> dict[str, str | int | bool]:
    """Issue a short-lived token for the speech WebSocket gateway."""
    if not resolve_ws_secret():
        return {"enabled": False}

    try:
        payload = create_ws_token()
        speech_settings = await resolve_speech_settings()
        return {
            **payload,
            "enabled": speech_settings.enabled,
        }
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
