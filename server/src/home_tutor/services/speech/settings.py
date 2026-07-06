"""Speech gateway settings and factory helpers."""

from __future__ import annotations

from dataclasses import dataclass

from home_tutor.core.config import settings
from home_tutor.services.speech.aliyun_client import AliyunSpeechConfig, create_nls_token
from home_tutor.services.speech.token_cache import get_or_create_token


@dataclass(frozen=True)
class SpeechGatewaySettings:
    """Resolved speech gateway configuration."""

    enabled: bool
    app_key: str
    token: str
    gateway_url: str
    tts_voice: str
    tts_format: str
    tts_sample_rate: int


async def resolve_speech_settings() -> SpeechGatewaySettings:
    """Build runtime speech settings from environment variables."""
    app_key = settings.aliyun_speech_app_key.strip()
    token = settings.aliyun_speech_token.strip()
    gateway_url = settings.aliyun_speech_gateway_url

    if not token and settings.aliyun_speech_access_key_id and settings.aliyun_speech_access_key_secret:
        token = await get_or_create_token(
            lambda: create_nls_token(
                access_key_id=settings.aliyun_speech_access_key_id,
                access_key_secret=settings.aliyun_speech_access_key_secret,
                region=settings.aliyun_speech_region,
            ),
        )

    enabled = bool(app_key) and bool(token)
    return SpeechGatewaySettings(
        enabled=enabled,
        app_key=app_key,
        token=token,
        gateway_url=gateway_url,
        tts_voice=settings.aliyun_speech_tts_voice,
        tts_format=settings.aliyun_speech_tts_format,
        tts_sample_rate=settings.aliyun_speech_tts_sample_rate,
    )


def to_aliyun_config(resolved: SpeechGatewaySettings) -> AliyunSpeechConfig:
    """Convert gateway settings to Alibaba client config."""
    return AliyunSpeechConfig(
        app_key=resolved.app_key,
        token=resolved.token,
        gateway_url=resolved.gateway_url,
        tts_voice=resolved.tts_voice,
        tts_format=resolved.tts_format,
        tts_sample_rate=resolved.tts_sample_rate,
    )
