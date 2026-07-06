"""Tests for CopilotKit FastAPI endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from home_tutor.main import create_app


@pytest.mark.asyncio
async def test_copilotkit_info_lists_tutor_agent() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/copilotkit/", follow_redirects=True)
        assert response.status_code == 200
        body = response.json()
        agent_names = [agent["name"] for agent in body.get("agents", [])]
        assert "tutor" in agent_names


@pytest.mark.asyncio
async def test_copilotkit_runtime_info_exposes_named_agents() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/copilotkit/info")
        assert response.status_code == 200
        body = response.json()
        assert "tutor" in body["agents"]
        assert body["agents"]["tutor"]["description"]
        assert "version" in body
