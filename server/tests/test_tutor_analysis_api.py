"""Tests for analyze and SSE endpoints."""

import json

from fastapi.testclient import TestClient

from home_tutor.main import app

client = TestClient(app)

SCORE50_SESSION = "a1000001-0001-4001-8001-000000000001"


def test_analyze_returns_503_when_llm_not_configured(monkeypatch) -> None:
    monkeypatch.setenv("LLM_ACTIVE_PROVIDER", "")
    res = client.post(f"/api/sessions/{SCORE50_SESSION}/questions/q01/analyze")
    assert res.status_code == 503


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
