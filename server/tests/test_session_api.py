"""Tests for session review API."""

from fastapi.testclient import TestClient

from home_tutor.main import app

client = TestClient(app)

SCORE50_SESSION = "a1000001-0001-4001-8001-000000000001"


def test_tutor_view_returns_30_questions() -> None:
    res = client.get(f"/api/sessions/{SCORE50_SESSION}/tutor-view")
    assert res.status_code == 200
    body = res.json()
    assert len(body["questions"]) == 30
    assert body["timeline_index"]["duration_ms"] > 0


def test_question_detail_q01() -> None:
    res = client.get(f"/api/sessions/{SCORE50_SESSION}/questions/q01")
    assert res.status_code == 200
    body = res.json()
    assert body["package"]["question_id"] == "q01"
    assert body["tutor"]["question_id"] == "q01"
