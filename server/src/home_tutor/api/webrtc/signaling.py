"""WebRTC signaling endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from home_tutor.core.logging import get_logger, log_trace

logger = get_logger(__name__)

router = APIRouter(tags=["webrtc"])


class IceServerConfig(BaseModel):
    """ICE server configuration for WebRTC clients."""

    urls: list[str]
    username: str | None = None
    credential: str | None = None


class SignalingConfig(BaseModel):
    """Signaling configuration returned to clients."""

    ice_servers: list[IceServerConfig]


@router.get("/config")
async def get_webrtc_config() -> SignalingConfig:
    """Return ICE server configuration for WebRTC peer connections."""
    return SignalingConfig(
        ice_servers=[
            IceServerConfig(urls=["stun:stun.l.google.com:19302"]),
        ]
    )


class SdpOffer(BaseModel):
    """SDP offer from client."""

    sdp: str
    type: str = "offer"


class SdpAnswer(BaseModel):
    """SDP answer from server."""

    sdp: str
    type: str = "answer"


@router.post("/offer")
async def handle_offer(offer: SdpOffer) -> dict[str, str]:
    """Handle WebRTC SDP offer — placeholder for aiortc integration."""
    log_trace(logger, "WEBRTC_OFFER", offer_type=offer.type)
    return {"status": "received", "message": "WebRTC signaling — implement with aiortc"}
