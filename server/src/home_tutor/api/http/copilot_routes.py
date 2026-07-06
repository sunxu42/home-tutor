"""CopilotKit compatibility routes for frontend runtime v2."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from home_tutor.services.tutor_chat.copilot_sdk import get_copilot_sdk

router = APIRouter(tags=["copilotkit"])


def _build_runtime_context(request: Request) -> dict[str, Any]:
    return {
        "properties": {},
        "frontend_url": str(request.headers.get("referer") or ""),
        "headers": request.headers,
    }


def build_runtime_info_payload(*, context: dict[str, Any]) -> dict[str, Any]:
    """Convert legacy CopilotKit SDK info into runtime v2 shape."""
    legacy = get_copilot_sdk().info(context=context)
    agents: dict[str, dict[str, Any]] = {}
    for agent in legacy.get("agents", []):
        if not isinstance(agent, dict):
            continue
        name = str(agent.get("name", "")).strip()
        if not name:
            continue
        agents[name] = {
            "description": str(agent.get("description", "")),
            "capabilities": agent.get("capabilities") or {},
        }

    return {
        "version": legacy.get("sdkVersion", ""),
        "agents": agents,
        "actions": legacy.get("actions", []),
    }


@router.get("/copilotkit/info")
async def get_copilotkit_runtime_info(request: Request) -> JSONResponse:
    """Expose CopilotKit runtime info in the shape expected by @copilotkit/react-core v2."""
    payload = build_runtime_info_payload(context=_build_runtime_context(request))
    return JSONResponse(content=payload)
