"""Tests for logging configuration and output."""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.testclient import TestClient

from home_tutor.api.middleware.logging import RequestLoggingMiddleware
from home_tutor.core.config import Settings
from home_tutor.core.logging import (
    DailyJsonFileHandler,
    LogModeFilter,
    cleanup_old_logs,
    get_logger,
    log_milestone,
    log_trace,
    redact_sensitive_fields,
    setup_logging,
)


def test_log_settings_defaults(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("LOG_MODE", raising=False)
    monkeypatch.delenv("LOG_LLM_VERBOSE", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    settings = Settings()
    assert settings.log_mode == "milestone"
    assert settings.log_dir == Path("data/logs")
    assert settings.log_file_enabled is True
    assert settings.log_console_enabled is True
    assert settings.log_retention_days == 30
    assert settings.log_llm_verbose is True


def test_log_mode_debug_sets_level(monkeypatch) -> None:
    monkeypatch.setenv("LOG_MODE", "debug")
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    settings = Settings()
    assert settings.resolved_log_level == "DEBUG"


def test_log_mode_milestone_sets_info_level(monkeypatch) -> None:
    monkeypatch.setenv("LOG_MODE", "milestone")
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    settings = Settings()
    assert settings.resolved_log_level == "INFO"


def test_daily_json_file_handler_writes_parseable_line(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    handler = DailyJsonFileHandler(log_dir)
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="",
        args=(),
        exc_info=None,
    )
    record.msg = json.dumps({
        "timestamp": "2026-06-30T10:00:00Z",
        "level": "info",
        "event": "TEST_EVENT",
    })
    handler.emit(record)
    handler.close()

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    log_file = log_dir / f"app-{today}.jsonl"
    assert log_file.exists()
    line = log_file.read_text(encoding="utf-8").strip()
    parsed = json.loads(line)
    assert parsed["event"] == "TEST_EVENT"
    assert "timestamp" in parsed
    assert "level" in parsed


def test_redact_sensitive_fields() -> None:
    data = {
        "api_key": "sk-secret",
        "authorization": "Bearer tok",
        "provider": "deepseek",
        "nested": {"secret_key": "xyz", "model": "gpt-4"},
    }
    redact_sensitive_fields(data)
    assert data["api_key"] == "***REDACTED***"
    assert data["authorization"] == "***REDACTED***"
    assert data["provider"] == "deepseek"
    assert data["nested"]["secret_key"] == "***REDACTED***"
    assert data["nested"]["model"] == "gpt-4"


def test_cleanup_old_log_files(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    old_file = log_dir / "app-2020-01-01.jsonl"
    old_file.write_text('{"event":"old"}\n', encoding="utf-8")
    old_ts = (datetime.now(UTC) - timedelta(days=60)).timestamp()
    os.utime(old_file, (old_ts, old_ts))

    cleanup_old_logs(log_dir, retention_days=30)

    assert not old_file.exists()


def _flush_handlers() -> None:
    for handler in logging.getLogger().handlers:
        handler.flush()
        handler.close()
    logging.getLogger().handlers.clear()


def test_setup_logging_writes_milestone_to_file(tmp_path: Path, monkeypatch) -> None:
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("LOG_DIR", str(log_dir))
    monkeypatch.setenv("LOG_FILE_ENABLED", "true")
    monkeypatch.setenv("LOG_CONSOLE_ENABLED", "false")
    monkeypatch.setenv("LOG_MODE", "milestone")

    setup_logging(Settings())
    log_milestone(get_logger("test"), "ANALYSIS_STARTED", session_id="s1", question_id="q1")

    _flush_handlers()

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    log_file = log_dir / f"app-{today}.jsonl"
    assert log_file.exists()
    parsed = json.loads(log_file.read_text(encoding="utf-8").strip())
    assert parsed["event"] == "ANALYSIS_STARTED"
    assert parsed["milestone"] is True


def test_milestone_mode_filters_trace_from_file(tmp_path: Path, monkeypatch) -> None:
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("LOG_DIR", str(log_dir))
    monkeypatch.setenv("LOG_CONSOLE_ENABLED", "false")
    monkeypatch.setenv("LOG_MODE", "milestone")

    setup_logging(Settings())
    log_trace(get_logger("test"), "HTTP_REQUEST", method="GET", path="/api/health")

    _flush_handlers()

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    log_file = log_dir / f"app-{today}.jsonl"
    assert not log_file.exists() or log_file.read_text(encoding="utf-8").strip() == ""


def test_log_milestone_sets_flag(tmp_path: Path, monkeypatch) -> None:
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("LOG_DIR", str(log_dir))
    monkeypatch.setenv("LOG_CONSOLE_ENABLED", "false")
    monkeypatch.setenv("LOG_MODE", "milestone")

    setup_logging(Settings())
    log_milestone(get_logger("test.milestone"), "ANALYSIS_STARTED", session_id="s1", question_id="q1")

    _flush_handlers()

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    line = (log_dir / f"app-{today}.jsonl").read_text(encoding="utf-8").strip().splitlines()[-1]
    parsed = json.loads(line)
    assert parsed["milestone"] is True
    assert parsed["event"] == "ANALYSIS_STARTED"
    assert parsed["session_id"] == "s1"


def test_request_logging_middleware_adds_request_id(tmp_path: Path, monkeypatch) -> None:
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("LOG_DIR", str(log_dir))
    monkeypatch.setenv("LOG_CONSOLE_ENABLED", "false")
    monkeypatch.setenv("LOG_MODE", "verbose")

    setup_logging(Settings())

    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        rid = structlog.contextvars.get_contextvars().get("request_id")
        get_logger("test.ping").info("inside_handler", marker="yes")
        return {"request_id": rid or ""}

    client = TestClient(app)
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")
    assert response.json()["request_id"] == response.headers.get("X-Request-ID")


def test_log_mode_filter_milestone_blocks_trace() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg={"event": "HTTP_REQUEST", "log_class": "trace"},
        args=(),
        exc_info=None,
    )
    record._name = "info"  # noqa: SLF001
    record._logger = logging.getLogger("test")  # noqa: SLF001

    assert LogModeFilter("milestone", "console").filter(record) is False
    assert LogModeFilter("verbose", "console").filter(record) is True


def test_log_llm_verbose_controls_prompt_fields(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LOG_DIR", str(tmp_path))
    monkeypatch.setenv("LOG_CONSOLE_ENABLED", "false")
    monkeypatch.setenv("LOG_LLM_VERBOSE", "false")

    settings = Settings()
    assert settings.log_llm_verbose is False

    monkeypatch.setenv("LOG_LLM_VERBOSE", "true")
    settings_verbose = Settings()
    assert settings_verbose.log_llm_verbose is True
