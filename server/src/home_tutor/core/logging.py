"""Structured logging setup for Home Tutor server."""

from __future__ import annotations

import contextvars
import json
import logging
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import structlog

from home_tutor.core.config import LogMode, Settings

request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)

_SENSITIVE_KEYS = frozenset({
    "api_key",
    "authorization",
    "secret",
    "secret_key",
    "password",
    "token",
    "access_token",
})

_MILESTONE_EVENTS = frozenset({
    "ANALYSIS_ENQUEUED",
    "ANALYSIS_STARTED",
    "LLM_REQUEST",
    "LLM_RESPONSE",
    "ANALYSIS_COMPLETE",
    "ANALYSIS_FAILED",
})

_TRACE_EVENTS = frozenset({
    "HTTP_REQUEST",
    "HTTP_RESPONSE",
    "LLM_PROMPT",
    "LLM_RESPONSE_BODY",
    "LANGFUSE_ENABLED",
    "LANGFUSE_DISABLED",
    "SERVER_STARTED",
    "WS_CONNECT",
    "WS_MESSAGE",
    "WEBRTC_OFFER",
})

_EVENT_SHORT_LABELS = {
    "ANALYSIS_ENQUEUED": "ENQUEUED",
    "ANALYSIS_STARTED": "STARTED",
    "LLM_REQUEST": "LLM_REQ",
    "LLM_RESPONSE": "LLM_RESP",
    "ANALYSIS_COMPLETE": "DONE",
    "ANALYSIS_FAILED": "FAILED",
}

_NOISY_LOGGERS = (
    "sqlalchemy",
    "sqlalchemy.engine",
    "sqlalchemy.engine.Engine",
    "aiosqlite",
    "asyncio",
    "httpx",
    "httpcore",
    "langfuse",
    "uvicorn.access",
)

# ANSI styles (terminal only)
_BOLD = "\033[1m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_DIM = "\033[2m"
_RESET = "\033[0m"


def redact_sensitive_fields(obj: Any) -> Any:
    """Recursively redact sensitive dict keys in place."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower() in _SENSITIVE_KEYS:
                obj[key] = "***REDACTED***"
            else:
                redact_sensitive_fields(value)
    elif isinstance(obj, list):
        for item in obj:
            redact_sensitive_fields(item)
    return obj


def _extract_event_dict(record: logging.LogRecord) -> dict[str, Any] | None:
    """Return structlog event dict attached by wrap_for_formatter."""
    if getattr(record, "_name", None) == "__structlog_sentinel__":
        return None
    if hasattr(record, "_logger") and isinstance(record.msg, dict):
        return record.msg
    return None


def _is_ops_event(event_dict: dict[str, Any]) -> bool:
    level = str(event_dict.get("level", "")).lower()
    if level in {"warning", "error", "critical"}:
        return True
    event = str(event_dict.get("event", ""))
    return event in {"HTTP_ERROR", "LLM_HTTP_ERROR"}


def _should_emit(event_dict: dict[str, Any] | None, *, mode: LogMode, target: str) -> bool:
    """Decide whether an event is written to console or file."""
    if event_dict is None:
        return mode == "debug"

    if _is_ops_event(event_dict):
        return True

    is_milestone = bool(event_dict.get("milestone")) or event_dict.get("event") in _MILESTONE_EVENTS
    is_trace = event_dict.get("log_class") == "trace" or event_dict.get("event") in _TRACE_EVENTS

    if target == "console":
        if mode == "debug":
            return True
        if is_milestone:
            return True
        if mode == "verbose" and is_trace:
            return True
        return False

    # file
    if mode == "debug":
        return True
    if is_milestone:
        return True
    if mode == "verbose" and is_trace:
        return True
    return False


class LogModeFilter(logging.Filter):
    """Filter log records by LOG_MODE and event class."""

    def __init__(self, mode: LogMode, target: str) -> None:
        super().__init__()
        self._mode = mode
        self._target = target

    def filter(self, record: logging.LogRecord) -> bool:
        return _should_emit(_extract_event_dict(record), mode=self._mode, target=self._target)


def _short_time(timestamp: str | None) -> str:
    if not timestamp:
        return datetime.now(UTC).strftime("%H:%M:%S")
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except ValueError:
        return timestamp[:8]


def _truncate(text: str, limit: int = 200) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return f"{text[:limit]}… ({len(text)} chars)"


def _format_milestone_line(event_dict: dict[str, Any]) -> str:
    event = str(event_dict.get("event", ""))
    label = _EVENT_SHORT_LABELS.get(event, event)
    parts: list[str] = []

    session_id = event_dict.get("session_id")
    question_id = event_dict.get("question_id")
    if session_id and question_id:
        parts.append(f"{session_id}/{question_id}")
    elif session_id:
        parts.append(str(session_id))

    for key in ("reason", "provider", "model", "verdict", "error"):
        if value := event_dict.get(key):
            if key == "model":
                parts.append(str(value))
            else:
                parts.append(f"{key}={value}")

    duration_ms = event_dict.get("duration_ms")
    if isinstance(duration_ms, (int, float)):
        parts.append(f"{duration_ms / 1000:.1f}s")

    tokens_in = event_dict.get("tokens_in")
    tokens_out = event_dict.get("tokens_out")
    if tokens_in is not None and tokens_out is not None:
        parts.append(f"tokens={tokens_in}→{tokens_out}")

    body = "  ".join(parts)
    line = f"{_short_time(event_dict.get('timestamp'))}  ▶ {label:<10} {body}".rstrip()
    return f"{_BOLD}{_GREEN}{line}{_RESET}"


def _format_trace_line(event_dict: dict[str, Any]) -> str:
    event = str(event_dict.get("event", ""))
    time_str = _short_time(event_dict.get("timestamp"))

    if event == "HTTP_REQUEST":
        line = f"{time_str}    → {event_dict.get('method')} {event_dict.get('path')}"
    elif event == "HTTP_RESPONSE":
        line = (
            f"{time_str}    ← {event_dict.get('status_code')}  "
            f"{event_dict.get('duration_ms')}ms"
        )
    elif event == "LLM_PROMPT":
        line = f"{time_str}    prompt: {_truncate(str(event_dict.get('prompt_preview', '')))}"
    elif event == "LLM_RESPONSE_BODY":
        line = (
            f"{time_str}    response: "
            f"verdict={event_dict.get('verdict')}  "
            f"summary={_truncate(str(event_dict.get('summary', '')), 80)}"
        )
    elif event in {"LANGFUSE_ENABLED", "SERVER_STARTED"}:
        details = "  ".join(
            f"{k}={v}" for k, v in event_dict.items()
            if k not in {"event", "timestamp", "level", "log_class", "milestone"}
        )
        line = f"{time_str}    {event.lower().replace('_', ' ')}  {details}".rstrip()
    else:
        details = "  ".join(
            f"{k}={v}" for k, v in event_dict.items()
            if k not in {"event", "timestamp", "level", "log_class", "milestone"}
        )
        line = f"{time_str}    {event}  {details}".rstrip()

    return f"{_DIM}{line}{_RESET}"


def _format_ops_line(event_dict: dict[str, Any]) -> str:
    event = str(event_dict.get("event", ""))
    time_str = _short_time(event_dict.get("timestamp"))
    level = str(event_dict.get("level", "info")).lower()
    details = "  ".join(
        f"{k}={v}" for k, v in event_dict.items()
        if k not in {"event", "timestamp", "level", "log_class", "milestone"}
    )
    line = f"{time_str}  ! {event}  {details}".rstrip()
    if level in {"error", "critical"}:
        return f"{_BOLD}{_RED}{line}{_RESET}"
    if level == "warning":
        return f"{_BOLD}{_YELLOW}{line}{_RESET}"
    return line


def _human_console_renderer(
    _logger: Any, _method: str, event_dict: dict[str, Any]
) -> str:
    """Render a single human-readable console line."""
    if event_dict.get("milestone") or event_dict.get("event") in _MILESTONE_EVENTS:
        return _format_milestone_line(event_dict)
    if _is_ops_event(event_dict):
        return _format_ops_line(event_dict)
    return _format_trace_line(event_dict)


def _redact_processor(
    _logger: Any, _method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    redact_sensitive_fields(event_dict)
    return event_dict


def _add_request_id_processor(
    _logger: Any, _method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    rid = request_id_ctx.get()
    if rid:
        event_dict["request_id"] = rid
    return event_dict


def _safe_json_serializer(obj: Any, **kwargs: Any) -> str:
    kwargs.setdefault("ensure_ascii", False)
    try:
        return json.dumps(obj, **kwargs)
    except (TypeError, ValueError):
        return json.dumps({"serialization_error": repr(obj)}, ensure_ascii=False)


class DailyJsonFileHandler(logging.Handler):
    """Write one JSON object per line to app-YYYY-MM-DD.jsonl."""

    def __init__(self, log_dir: Path) -> None:
        super().__init__()
        self._log_dir = log_dir
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._current_date: str = ""
        self._file: Any = None

    def _ensure_file(self) -> None:
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        if today != self._current_date:
            if self._file is not None:
                self._file.close()
            self._current_date = today
            path = self._log_dir / f"app-{today}.jsonl"
            self._file = open(path, "a", encoding="utf-8")  # noqa: SIM115

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._ensure_file()
            msg = self.format(record)
            self._file.write(msg + "\n")
            self._file.flush()
        except OSError:
            self.handleError(record)

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None
        super().close()


def cleanup_old_logs(log_dir: Path, *, retention_days: int) -> None:
    """Delete app-*.jsonl files older than retention_days."""
    if not log_dir.exists():
        return
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    for path in log_dir.glob("app-*.jsonl"):
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        if mtime < cutoff:
            path.unlink(missing_ok=True)


def set_request_id(request_id: str | None) -> contextvars.Token[str | None]:
    """Bind request_id for current async context."""
    return request_id_ctx.set(request_id)


def reset_request_id(token: contextvars.Token[str | None]) -> None:
    """Reset request_id context."""
    request_id_ctx.reset(token)


def _configure_third_party_loggers(mode: LogMode) -> None:
    """Silence noisy libraries unless LOG_MODE=debug."""
    if mode == "debug":
        level = logging.DEBUG
        access_level = logging.INFO
    elif mode == "verbose":
        level = logging.WARNING
        access_level = logging.WARNING
    else:
        level = logging.ERROR
        access_level = logging.ERROR

    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(level)

    logging.getLogger("uvicorn.access").setLevel(access_level)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def setup_logging(settings: Settings) -> None:
    """Configure structlog and stdlib logging. Safe to call multiple times."""
    mode = settings.log_mode
    file_enabled = settings.log_file_enabled
    try:
        if file_enabled:
            settings.log_dir.mkdir(parents=True, exist_ok=True)
            cleanup_old_logs(settings.log_dir, retention_days=settings.log_retention_days)
    except OSError:
        file_enabled = False

    level = getattr(logging, settings.resolved_log_level, logging.INFO)
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        _add_request_id_processor,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        _redact_processor,
        structlog.processors.UnicodeDecoder(),
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    json_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(serializer=_safe_json_serializer),
        ],
    )

    console_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            _human_console_renderer,
        ],
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    if settings.log_console_enabled:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(LogModeFilter(mode, "console"))
        root.addHandler(console_handler)

    if file_enabled:
        try:
            file_handler = DailyJsonFileHandler(settings.log_dir)
            file_handler.setLevel(level)
            file_handler.setFormatter(json_formatter)
            file_handler.addFilter(LogModeFilter(mode, "file"))
            root.addHandler(file_handler)
        except OSError:
            pass

    _configure_third_party_loggers(mode)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger bound to the given module name."""
    return structlog.get_logger(name)


def log_milestone(
    logger: structlog.stdlib.BoundLogger,
    event: str,
    **kwargs: Any,
) -> None:
    """Log a milestone event (always visible in milestone mode)."""
    logger.info(event, milestone=True, **kwargs)


def log_trace(
    logger: structlog.stdlib.BoundLogger,
    event: str,
    **kwargs: Any,
) -> None:
    """Log a trace event (visible in verbose/debug mode)."""
    logger.info(event, log_class="trace", **kwargs)
