"""Tests for analyze and SSE endpoints."""

import json
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from home_tutor.api.deps import get_analysis_service
from home_tutor.main import app

client = TestClient(app)

SCORE50_SESSION = "a1000001-0001-4001-8001-000000000001"


def test_analyze_returns_503_when_llm_not_configured() -> None:
    mock_analysis = MagicMock()
    mock_analysis.llm_settings.is_configured.return_value = False
    app.dependency_overrides[get_analysis_service] = lambda: mock_analysis
    try:
        res = client.post(f"/api/sessions/{SCORE50_SESSION}/questions/q01/analyze")
        assert res.status_code == 503
    finally:
        app.dependency_overrides.clear()


def test_question_detail_includes_analysis_status() -> None:
    res = client.get(f"/api/sessions/{SCORE50_SESSION}/questions/q01")
    assert res.status_code == 200
    tutor = res.json()["tutor"]
    assert tutor["analysis_status"] in {"ready", "missing", "generating", "failed"}


def test_tutor_sse_returns_ready_event() -> None:
    with client.stream(
        "GET",
        f"/api/sessions/{SCORE50_SESSION}/questions/q01/tutor/events",
    ) as response:
        assert response.status_code == 200
        chunks = "".join(response.iter_text())
    assert "event: tutor" in chunks or "event: status" in chunks
