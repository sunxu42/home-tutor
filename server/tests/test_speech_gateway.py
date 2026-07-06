"""Speech gateway websocket tests."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from home_tutor.core.config import settings
from home_tutor.main import create_app
from home_tutor.services.speech.settings import SpeechGatewaySettings
from home_tutor.services.speech.ws_token import create_ws_token

PartialHandler = Callable[[str], Awaitable[None] | None]
FinalHandler = Callable[[str], Awaitable[None] | None]
AudioHandler = Callable[[bytes], Awaitable[None] | None]
ErrorHandler = Callable[[str], Awaitable[None] | None]


def _speech_settings(*, enabled: bool) -> SpeechGatewaySettings:
    return SpeechGatewaySettings(
        enabled=enabled,
        app_key="test-app-key",
        token="test-token",
        gateway_url="wss://example.test/ws/v1",
        tts_voice="xiaoyun",
        tts_format="pcm",
        tts_sample_rate=16000,
    )


def _speech_ws_url() -> str:
    token = create_ws_token()["token"]
    return f"/ws/speech?token={token}"


@pytest.fixture(autouse=True)
def speech_ws_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "speech_ws_secret", "test-speech-secret")


class FakeAsrSession:
    def __init__(self, _config: Any) -> None:
        self._on_partial: PartialHandler | None = None
        self._on_final: FinalHandler | None = None

    async def start(
        self,
        *,
        on_partial: PartialHandler,
        on_final: FinalHandler,
        on_error: ErrorHandler,
    ) -> None:
        self._on_partial = on_partial
        self._on_final = on_final
        _ = on_error

    async def send_audio(self, chunk: bytes) -> None:
        if self._on_partial and len(chunk) > 0:
            result = self._on_partial("正在听你说…")
            if hasattr(result, "__await__"):
                await result

    async def stop(self) -> None:
        if self._on_final:
            result = self._on_final("请帮我详细讲讲这道题")
            if hasattr(result, "__await__"):
                await result

    async def close(self) -> None:
        return None


class FakeTtsSession:
    def __init__(self, _config: Any) -> None:
        self._on_audio: AudioHandler | None = None

    async def synthesize(
        self,
        text: str,
        *,
        on_audio: AudioHandler,
        on_error: ErrorHandler,
    ) -> None:
        _ = text
        _ = on_error
        self._on_audio = on_audio
        result = on_audio(b"\x00\x01" * 100)
        if hasattr(result, "__await__"):
            await result

    async def stop(self) -> None:
        return None

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_speech_gateway_asr_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_resolve() -> SpeechGatewaySettings:
        return _speech_settings(enabled=True)

    monkeypatch.setattr(
        "home_tutor.services.speech.gateway.resolve_speech_settings",
        fake_resolve,
    )
    monkeypatch.setattr("home_tutor.services.speech.gateway.AliyunAsrSession", FakeAsrSession)

    app = create_app()
    client = TestClient(app)
    with client.websocket_connect(_speech_ws_url()) as websocket:
        ready = json.loads(websocket.receive_text())
        assert ready == {"type": "ready", "enabled": True}

        websocket.send_text(json.dumps({"type": "asr_start"}))
        assert json.loads(websocket.receive_text()) == {"type": "asr_started"}

        websocket.send_bytes(b"\x00\x01" * 2000)
        websocket.send_text(json.dumps({"type": "asr_stop"}))
        partial = json.loads(websocket.receive_text())
        assert partial == {"type": "asr_partial", "text": "正在听你说…"}
        final = json.loads(websocket.receive_text())
        assert final == {"type": "asr_final", "text": "请帮我详细讲讲这道题"}
        assert json.loads(websocket.receive_text()) == {"type": "asr_stopped"}


@pytest.mark.asyncio
async def test_speech_gateway_tts_emits_audio(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_resolve() -> SpeechGatewaySettings:
        return _speech_settings(enabled=True)

    monkeypatch.setattr(
        "home_tutor.services.speech.gateway.resolve_speech_settings",
        fake_resolve,
    )
    monkeypatch.setattr("home_tutor.services.speech.gateway.AliyunTtsSession", FakeTtsSession)

    app = create_app()
    client = TestClient(app)
    with client.websocket_connect(_speech_ws_url()) as websocket:
        json.loads(websocket.receive_text())

        websocket.send_text(
            json.dumps({"type": "tts_start", "text": "你好", "utteranceId": "u1"}),
        )
        assert json.loads(websocket.receive_text()) == {
            "type": "tts_started",
            "utteranceId": "u1",
        }
        audio = websocket.receive_bytes()
        assert len(audio) > 0
        ended = json.loads(websocket.receive_text())
        assert ended == {"type": "tts_ended", "utteranceId": "u1"}


@pytest.mark.asyncio
async def test_speech_gateway_disabled_when_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_resolve() -> SpeechGatewaySettings:
        return _speech_settings(enabled=False)

    monkeypatch.setattr(
        "home_tutor.services.speech.gateway.resolve_speech_settings",
        fake_resolve,
    )

    app = create_app()
    client = TestClient(app)
    with client.websocket_connect(_speech_ws_url()) as websocket:
        ready = json.loads(websocket.receive_text())
        assert ready == {"type": "ready", "enabled": False}
        with pytest.raises(WebSocketDisconnect):
            websocket.receive_text()


@pytest.mark.asyncio
async def test_speech_gateway_rejects_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_resolve() -> SpeechGatewaySettings:
        return _speech_settings(enabled=True)

    monkeypatch.setattr(
        "home_tutor.services.speech.gateway.resolve_speech_settings",
        fake_resolve,
    )

    app = create_app()
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/speech"):
            pass
