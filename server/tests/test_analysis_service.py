"""Tests for tutor analysis orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest

from home_tutor.services.analysis.session_store import SessionStore
from home_tutor.services.llm.analysis_service import TutorAnalysisService
from home_tutor.services.llm.config import LlmProviderConfig, LlmSettings
from home_tutor.services.llm.tutor_generator import TutorGenerator


@pytest.fixture
def session_dir(tmp_path: Path) -> Path:
    session_id = "test-session-0001-0001-0001-000000000001"
    root = tmp_path / "sessions"
    sdir = root / "live"
    sdir.mkdir(parents=True)
    (sdir / "packages").mkdir()
    (sdir / "tutor").mkdir()
    (sdir / "meta.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "questions": [{"question_id": "q01", "number": 1}],
                "metadata": {"data_source": "live"},
            }
        ),
        encoding="utf-8",
    )
    package = {
        "schema_version": "home-tutor.question-package.v1",
        "session_id": session_id,
        "question_id": "q01",
        "number": 1,
        "prompt": {"text": "1+1=?"},
        "final_answer": {"text": "3"},
        "answer_timeline": [],
        "focus_segments": [],
        "process_metrics": {"active_duration_ms": 1000, "revision_count": 0},
    }
    (sdir / "packages" / "q01.json").write_text(json.dumps(package), encoding="utf-8")
    return root


def _settings(*, save_token: bool = False, skip_fixture: bool = False) -> LlmSettings:
    return LlmSettings(
        active_provider="mock",
        save_token_mode=save_token,
        skip_fixture_tutor=skip_fixture,
        request_timeout_sec=5.0,
        providers={
            "mock": LlmProviderConfig(
                name="mock",
                api_key="sk-test",
                base_url="https://example.com/v1",
                model="mock-model",
            )
        },
    )


@pytest.mark.asyncio
async def test_schedule_writes_ready_tutor(session_dir: Path) -> None:
    store = SessionStore(session_dir)
    session_id = "test-session-0001-0001-0001-000000000001"

    generator = TutorGenerator()
    generator.generate = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "schema_version": "home-tutor.tutor-content.v1",
            "session_id": session_id,
            "question_id": "q01",
            "analysis_status": "ready",
            "verdict": "wrong",
            "reference_answer": "2",
            "summary": "再算算",
            "explanation_paragraphs": ["1+1=2"],
            "stale": False,
            "error": None,
        }
    )

    service = TutorAnalysisService(
        store=store,
        llm_settings=_settings(),
        generator=generator,
    )

    status = await service.schedule(session_id, "q01", reason="test", force=True)
    assert status == "generating"
    await _wait_for_ready(service, session_id, "q01")

    tutor = store.read_tutor(session_id, "q01")
    assert tutor["analysis_status"] == "ready"
    assert tutor["verdict"] == "wrong"


@pytest.mark.asyncio
async def test_analysis_service_uses_llm_request_timeout_for_client(session_dir: Path) -> None:
    store = SessionStore(session_dir)
    service = TutorAnalysisService(store=store, llm_settings=_settings())

    assert service.generator is not None
    assert service.generator._client._timeout == 5.0


@pytest.mark.asyncio
async def test_save_token_mode_writes_missing(session_dir: Path) -> None:
    store = SessionStore(session_dir)
    session_id = "test-session-0001-0001-0001-000000000001"
    service = TutorAnalysisService(store=store, llm_settings=_settings(save_token=True))

    status = await service.schedule(session_id, "q01", reason="test")
    assert status == "missing"
    tutor = store.read_tutor(session_id, "q01")
    assert tutor["analysis_status"] == "missing"


@pytest.fixture
def mock_session_dir(tmp_path: Path) -> Path:
    session_id = "mock-session-0001-0001-0001-000000000001"
    root = tmp_path / "sessions"
    sdir = root / "mock"
    sdir.mkdir(parents=True)
    (sdir / "packages").mkdir()
    (sdir / "tutor").mkdir()
    (sdir / "meta.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "questions": [{"question_id": "q01", "number": 1}],
                "metadata": {"data_source": "mock"},
            }
        ),
        encoding="utf-8",
    )
    package = {
        "schema_version": "home-tutor.question-package.v1",
        "session_id": session_id,
        "question_id": "q01",
        "number": 1,
        "prompt": {"text": "1+1=?"},
        "final_answer": {"text": "3"},
        "answer_timeline": [],
        "focus_segments": [],
        "process_metrics": {"active_duration_ms": 1000, "revision_count": 0},
    }
    tutor = {
        "schema_version": "home-tutor.tutor-content.v1",
        "session_id": session_id,
        "question_id": "q01",
        "analysis_status": "ready",
        "verdict": "wrong",
        "reference_answer": "2",
        "summary": "示例",
        "explanation_paragraphs": ["mock"],
        "model": "mock-v2",
        "stale": False,
    }
    (sdir / "packages" / "q01.json").write_text(json.dumps(package), encoding="utf-8")
    (sdir / "tutor" / "q01.json").write_text(json.dumps(tutor), encoding="utf-8")
    return root


@pytest.mark.asyncio
async def test_mock_session_skips_auto_schedule(mock_session_dir: Path) -> None:
    store = SessionStore(mock_session_dir)
    session_id = "mock-session-0001-0001-0001-000000000001"
    generator = TutorGenerator()
    generator.generate = AsyncMock()  # type: ignore[method-assign]

    service = TutorAnalysisService(store=store, llm_settings=_settings(), generator=generator)
    status = await service.schedule(session_id, "q01", reason="view")
    assert status == "ready"
    generator.generate.assert_not_called()


@pytest.mark.asyncio
async def test_mock_session_allows_manual_schedule(mock_session_dir: Path) -> None:
    store = SessionStore(mock_session_dir)
    session_id = "mock-session-0001-0001-0001-000000000001"
    generator = TutorGenerator()
    generator.generate = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "schema_version": "home-tutor.tutor-content.v1",
            "session_id": session_id,
            "question_id": "q01",
            "analysis_status": "ready",
            "verdict": "wrong",
            "reference_answer": "2",
            "summary": "LLM",
            "explanation_paragraphs": ["from llm"],
            "stale": False,
            "error": None,
        }
    )

    service = TutorAnalysisService(store=store, llm_settings=_settings(), generator=generator)
    status = await service.schedule(session_id, "q01", reason="manual_analyze", force=True)
    assert status == "generating"
    await _wait_for_ready(service, session_id, "q01")
    generator.generate.assert_called_once()


async def _wait_for_ready(
    service: TutorAnalysisService,
    session_id: str,
    question_id: str,
    *,
    attempts: int = 20,
) -> None:
    for _ in range(attempts):
        if (session_id, question_id) not in service._inflight:
            return
        import asyncio

        await asyncio.sleep(0.05)
    raise AssertionError("analysis did not finish in time")
