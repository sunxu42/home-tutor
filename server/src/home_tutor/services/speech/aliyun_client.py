"""Alibaba Cloud Intelligent Speech Interaction (NLS) WebSocket client."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import hashlib
import hmac
import json
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

import httpx
import websockets
from websockets.asyncio.client import ClientConnection

from home_tutor.core.logging import get_logger

logger = get_logger(__name__)

PartialHandler = Callable[[str], Awaitable[None] | None]
FinalHandler = Callable[[str], Awaitable[None] | None]
AudioHandler = Callable[[bytes], Awaitable[None] | None]
ErrorHandler = Callable[[str], Awaitable[None] | None]


@dataclass(frozen=True)
class AliyunSpeechConfig:
    """Runtime configuration for Alibaba NLS."""

    app_key: str
    token: str
    gateway_url: str = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
    tts_voice: str = "xiaoyun"
    tts_format: str = "pcm"
    tts_sample_rate: int = 16000


def _percent_encode(value: str) -> str:
    return quote(value, safe="~")


def _sign_rpc(params: dict[str, str], access_key_secret: str) -> str:
    canonical = "&".join(
        f"{_percent_encode(key)}={_percent_encode(value)}" for key, value in sorted(params.items())
    )
    string_to_sign = f"GET&{_percent_encode('/')}&{_percent_encode(canonical)}"
    digest = hmac.new(
        f"{access_key_secret}&".encode(),
        string_to_sign.encode(),
        hashlib.sha1,
    ).digest()
    return base64.b64encode(digest).decode()


async def create_nls_token(
    *,
    access_key_id: str,
    access_key_secret: str,
    region: str = "cn-shanghai",
) -> str:
    """Fetch a short-lived NLS token from Alibaba meta service."""
    params = {
        "AccessKeyId": access_key_id,
        "Action": "CreateToken",
        "Format": "JSON",
        "RegionId": region,
        "SignatureMethod": "HMAC-SHA1",
        "SignatureNonce": str(uuid.uuid4()),
        "SignatureVersion": "1.0",
        "Timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "Version": "2019-02-28",
    }
    params["Signature"] = _sign_rpc(params, access_key_secret)
    url = f"https://nls-meta.{region}.aliyuncs.com/"
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
    token = payload.get("Token", {}).get("Id")
    if not isinstance(token, str) or not token:
        raise RuntimeError("Failed to obtain Alibaba NLS token")
    return token


def _new_header(*, namespace: str, name: str, app_key: str, task_id: str) -> dict[str, str]:
    return {
        "message_id": str(uuid.uuid4()),
        "task_id": task_id,
        "namespace": namespace,
        "name": name,
        "appkey": app_key,
    }


class AliyunAsrSession:
    """One-shot real-time ASR session over NLS WebSocket."""

    def __init__(self, config: AliyunSpeechConfig) -> None:
        self._config = config
        self._task_id = str(uuid.uuid4())
        self._ws: ClientConnection | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._started = asyncio.Event()

    async def start(
        self,
        *,
        on_partial: PartialHandler,
        on_final: FinalHandler,
        on_error: ErrorHandler,
    ) -> None:
        url = f"{self._config.gateway_url}?token={self._config.token}"
        self._ws = await websockets.connect(url, open_timeout=15)
        self._reader_task = asyncio.create_task(
            self._read_loop(on_partial=on_partial, on_final=on_final, on_error=on_error),
        )
        await self._send_json(
            {
                "header": _new_header(
                    namespace="SpeechTranscriber",
                    name="StartTranscription",
                    app_key=self._config.app_key,
                    task_id=self._task_id,
                ),
                "payload": {
                    "format": "pcm",
                    "sample_rate": 16000,
                    "enable_intermediate_result": True,
                    "enable_punctuation_prediction": True,
                    "enable_inverse_text_normalization": True,
                },
            },
        )
        await asyncio.wait_for(self._started.wait(), timeout=10)

    async def send_audio(self, chunk: bytes) -> None:
        if self._ws is None:
            return
        await self._ws.send(chunk)

    async def stop(self) -> None:
        if self._ws is None:
            return
        await self._send_json(
            {
                "header": _new_header(
                    namespace="SpeechTranscriber",
                    name="StopTranscription",
                    app_key=self._config.app_key,
                    task_id=self._task_id,
                ),
            },
        )

    async def close(self) -> None:
        if self._reader_task is not None:
            self._reader_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reader_task
            self._reader_task = None
        if self._ws is not None:
            await self._ws.close()
            self._ws = None

    async def _send_json(self, payload: dict[str, Any]) -> None:
        if self._ws is None:
            raise RuntimeError("ASR websocket is not connected")
        await self._ws.send(json.dumps(payload, ensure_ascii=False))

    async def _read_loop(
        self,
        *,
        on_partial: PartialHandler,
        on_final: FinalHandler,
        on_error: ErrorHandler,
    ) -> None:
        assert self._ws is not None
        try:
            async for message in self._ws:
                if isinstance(message, bytes):
                    continue
                payload = json.loads(message)
                header = payload.get("header", {})
                name = header.get("name")
                status = header.get("status")
                if status not in (None, 20000000, "20000000"):
                    status_text = header.get("status_text", "ASR error")
                    await _maybe_await(on_error, str(status_text))
                    continue
                if name == "TranscriptionStarted":
                    self._started.set()
                elif name == "TranscriptionResultChanged":
                    text = payload.get("payload", {}).get("result", "")
                    if text:
                        await _maybe_await(on_partial, str(text))
                elif name in {"SentenceEnd", "TranscriptionCompleted"}:
                    text = payload.get("payload", {}).get("result", "")
                    if text:
                        await _maybe_await(on_final, str(text))
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning("ASR reader stopped", exc_info=exc)
            await _maybe_await(on_error, str(exc))


class AliyunTtsSession:
    """Streaming TTS synthesis session."""

    def __init__(self, config: AliyunSpeechConfig) -> None:
        self._config = config
        self._task_id = str(uuid.uuid4())
        self._ws: ClientConnection | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._started = asyncio.Event()
        self._completed = asyncio.Event()

    async def synthesize(
        self,
        text: str,
        *,
        on_audio: AudioHandler,
        on_error: ErrorHandler,
    ) -> None:
        url = f"{self._config.gateway_url}?token={self._config.token}"
        self._ws = await websockets.connect(url, open_timeout=15)
        self._reader_task = asyncio.create_task(
            self._read_loop(on_audio=on_audio, on_error=on_error),
        )
        await self._send_json(
            {
                "header": _new_header(
                    namespace="SpeechSynthesizer",
                    name="StartSynthesis",
                    app_key=self._config.app_key,
                    task_id=self._task_id,
                ),
                "payload": {
                    "text": text,
                    "voice": self._config.tts_voice,
                    "format": self._config.tts_format,
                    "sample_rate": self._config.tts_sample_rate,
                },
            },
        )
        await asyncio.wait_for(self._started.wait(), timeout=10)
        await asyncio.wait_for(self._completed.wait(), timeout=60)

    async def stop(self) -> None:
        if self._ws is None:
            return
        await self._send_json(
            {
                "header": _new_header(
                    namespace="SpeechSynthesizer",
                    name="StopSynthesis",
                    app_key=self._config.app_key,
                    task_id=self._task_id,
                ),
            },
        )

    async def close(self) -> None:
        if self._reader_task is not None:
            self._reader_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reader_task
            self._reader_task = None
        if self._ws is not None:
            await self._ws.close()
            self._ws = None

    async def _send_json(self, payload: dict[str, Any]) -> None:
        if self._ws is None:
            raise RuntimeError("TTS websocket is not connected")
        await self._ws.send(json.dumps(payload, ensure_ascii=False))

    async def _read_loop(self, *, on_audio: AudioHandler, on_error: ErrorHandler) -> None:
        assert self._ws is not None
        try:
            async for message in self._ws:
                if isinstance(message, bytes):
                    await _maybe_await(on_audio, message)
                    continue
                payload = json.loads(message)
                header = payload.get("header", {})
                name = header.get("name")
                status = header.get("status")
                if status not in (None, 20000000, "20000000"):
                    status_text = header.get("status_text", "TTS error")
                    await _maybe_await(on_error, str(status_text))
                    continue
                if name == "SynthesisStarted":
                    self._started.set()
                elif name == "SynthesisCompleted":
                    self._completed.set()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning("TTS reader stopped", exc_info=exc)
            await _maybe_await(on_error, str(exc))


async def _maybe_await(handler: Callable[..., Awaitable[None] | None], value: str | bytes) -> None:
    result = handler(value)
    if asyncio.iscoroutine(result):
        await result
