"""Speech WebSocket routes."""

from fastapi import APIRouter, WebSocket

from home_tutor.services.speech.gateway import handle_speech_websocket

router = APIRouter(tags=["speech"])


@router.websocket("/ws/speech")
async def speech_websocket(websocket: WebSocket) -> None:
    """Bidirectional speech gateway for ASR/TTS."""
    await handle_speech_websocket(websocket)
