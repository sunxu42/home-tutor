"""CopilotKit remote endpoint singleton."""

from __future__ import annotations

from copilotkit import CopilotKitRemoteEndpoint

from home_tutor.services.tutor_chat.copilot_graph import build_tutor_agent

_sdk: CopilotKitRemoteEndpoint | None = None


def get_copilot_sdk() -> CopilotKitRemoteEndpoint:
    """Return the shared CopilotKit SDK with the tutor agent registered."""
    global _sdk
    if _sdk is None:
        _sdk = CopilotKitRemoteEndpoint(agents=[build_tutor_agent()])
    return _sdk
