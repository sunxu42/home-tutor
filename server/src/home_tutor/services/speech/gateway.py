"""Bridge browser speech websocket to Alibaba NLS."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import WebSocket

from home_tutor.core.logging import get_logger
from home_tutor.services.speech.aliyun_client import AliyunAsrSession, AliyunTtsSession
from home_tutor.services.speech.settings import (
    SpeechGatewaySettings,
    resolve_speech_settings,
    to_aliyun_config,
)
from home_tutor.services.speech.ws_token import validate_ws_token

logger = get_logger(__name__)


class SpeechGateway:
    """Per-client speech session."""

    def __init__(self, websocket: WebSocket, settings: SpeechGatewaySettings) -> None:
        self._websocket = websocket
        self._settings = settings
        self._asr: AliyunAsrSession | None = None
        self._tts: AliyunTtsSession | None = None
        self._tts_task: asyncio.Task[None] | None = None
        self._asr_active = False

    async def run(self) -> None:
        await self._send_json(
            {
                "type": "ready",
                "enabled": self._settings.enabled,
            },
        )
        while True:
            message = await self._websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            if message.get("type") != "websocket.receive":
                continue
            data = message.get("text")
            if data is not None:
                await self._handle_text(data)
                continue
            audio = message.get("bytes")
            if audio is not None:
                await self._handle_audio(audio)

        await self.cleanup()

    async def _handle_text(self, raw: str) -> None:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            await self._send_error("invalid_json", "Invalid JSON frame")
            return
        if not isinstance(payload, dict):
            await self._send_error("invalid_payload", "Expected JSON object")
            return

        msg_type = payload.get("type")
        if msg_type == "asr_start":
            await self._start_asr()
        elif msg_type == "asr_stop":
            await self._stop_asr()
        elif msg_type == "tts_start":
            text = str(payload.get("text", "")).strip()
            utterance_id = str(payload.get("utteranceId", "")).strip() or "utt-1"
            if text:
                await self._start_tts(text=text, utterance_id=utterance_id)
        elif msg_type == "tts_stop":
            await self._stop_tts()
        elif msg_type == "ping":
            await self._send_json({"type": "pong"})
        else:
            await self._send_error("unknown_type", f"Unknown message type: {msg_type}")

    async def _handle_audio(self, chunk: bytes) -> None:
        if not self._asr_active or self._asr is None:
            return
        await self._asr.send_audio(chunk)

    async def _start_asr(self) -> None:
        if self._asr_active:
            return
        self._asr_active = True
        await self._send_json({"type": "asr_started"})

        config = to_aliyun_config(self._settings)
        self._asr = AliyunAsrSession(config)

        async def on_partial(text: str) -> None:
            await self._send_json({"type": "asr_partial", "text": text})

        async def on_final(text: str) -> None:
            await self._send_json({"type": "asr_final", "text": text})

        async def on_error(message: str) -> None:
            await self._send_error("asr_error", message)

        try:
            await self._asr.start(on_partial=on_partial, on_final=on_final, on_error=on_error)
        except Exception as exc:  # noqa: BLE001
            logger.warning("ASR start failed", exc_info=exc)
            self._asr_active = False
            await self._send_error("asr_start_failed", str(exc))

    async def _stop_asr(self) -> None:
        if not self._asr_active:
            return
        self._asr_active = False

        if self._asr is not None:
            try:
                await self._asr.stop()
            except Exception as exc:  # noqa: BLE001
                logger.warning("ASR stop failed", exc_info=exc)
                await self._send_error("asr_stop_failed", str(exc))
            finally:
                await self._asr.close()
                self._asr = None
        await self._send_json({"type": "asr_stopped"})

    async def _start_tts(self, *, text: str, utterance_id: str) -> None:
        await self._stop_tts()
        await self._send_json({"type": "tts_started", "utteranceId": utterance_id})

        config = to_aliyun_config(self._settings)
        self._tts = AliyunTtsSession(config)

        async def run_tts() -> None:
            assert self._tts is not None

            async def on_audio(chunk: bytes) -> None:
                await self._websocket.send_bytes(chunk)

            async def on_error(message: str) -> None:
                await self._send_error("tts_error", message)

            try:
                await self._tts.synthesize(text, on_audio=on_audio, on_error=on_error)
            except Exception as exc:  # noqa: BLE001
                logger.warning("TTS failed", exc_info=exc)
                await self._send_error("tts_failed", str(exc))
            finally:
                await self._tts.close()
                self._tts = None
                await self._send_json({"type": "tts_ended", "utteranceId": utterance_id})

        self._tts_task = asyncio.create_task(run_tts())

    async def _stop_tts(self) -> None:
        if self._tts_task is not None:
            self._tts_task.cancel()
            try:
                await self._tts_task
            except asyncio.CancelledError:
                pass
            self._tts_task = None
        if self._tts is not None:
            try:
                await self._tts.stop()
            except Exception:  # noqa: BLE001
                pass
            await self._tts.close()
            self._tts = None

    async def cleanup(self) -> None:
        if self._asr_active:
            await self._stop_asr()
        await self._stop_tts()

    async def _send_json(self, payload: dict[str, Any]) -> None:
        await self._websocket.send_text(json.dumps(payload, ensure_ascii=False))

    async def _send_error(self, code: str, message: str) -> None:
        await self._send_json({"type": "error", "code": code, "message": message})


async def handle_speech_websocket(websocket: WebSocket) -> None:
    """Entry point for `/ws/speech`."""
    token = websocket.query_params.get("token", "")
    if not validate_ws_token(token):
        await websocket.close(code=1008, reason="Invalid or missing speech token")
        return

    await websocket.accept()
    settings = await resolve_speech_settings()
    if not settings.enabled:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "ready",
                    "enabled": False,
                },
                ensure_ascii=False,
            ),
        )
        await websocket.close(code=1008, reason="Speech gateway disabled")
        return

    gateway = SpeechGateway(websocket, settings)
    try:
        await gateway.run()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Speech gateway disconnected", exc_info=exc)
    finally:
        await gateway.cleanup()
