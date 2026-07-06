"""Tests for fixture session seeding."""

from fastapi.testclient import TestClient

from home_tutor.main import app

client = TestClient(app)

FIXTURE_SESSION_IDS = {
    "a1000000-0000-4000-8000-000000000000",  # score48
    "a1000001-0001-4001-8001-000000000001",  # score53
    "a1000002-0002-4002-8002-000000000002",  # score58
    "a1000003-0003-4003-8003-000000000003",  # score62
    "b2000001-0001-4001-8001-000000000001",  # score68
    "b2000002-0002-4002-8002-000000000002",  # score73
    "b2000003-0003-4003-8003-000000000003",  # score78
    "c3000001-0001-4001-8001-000000000001",  # score85
    "c3000002-0002-4002-8002-000000000002",  # score92
    "c3000003-0003-4003-8003-000000000003",  # score96
}


def test_list_sessions_excludes_orphan_db_rows() -> None:
    res = client.get("/api/sessions")
    assert res.status_code == 200
    body = res.json()
    ids = {item["id"] for item in body}
    assert FIXTURE_SESSION_IDS.issubset(ids)
    assert "f0000001-0001-4001-8001-000000000099" not in ids


def test_list_sessions_includes_fixture_seeds() -> None:
    res = client.get("/api/sessions")
    assert res.status_code == 200
    body = res.json()
    ids = {item["id"] for item in body}
    assert FIXTURE_SESSION_IDS.issubset(ids)


def test_fixture_session_links_to_tutor_view() -> None:
    for session_id in FIXTURE_SESSION_IDS:
        res = client.get(f"/api/sessions/{session_id}/tutor-view")
        assert res.status_code == 200, session_id
        assert len(res.json()["questions"]) == 30
