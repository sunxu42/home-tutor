"""Application configuration."""

from pathlib import Path
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

LogMode = Literal["milestone", "verbose", "debug"]


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Home Tutor API"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173"]

    session_fixtures_root: Path = Path("tests/fixtures/sessions")
    data_dir: Path = Path("data")

    # Logging
    log_mode: LogMode = "milestone"
    log_level: str | None = None
    log_dir: Path = Path("data/logs")
    log_file_enabled: bool = True
    log_console_enabled: bool = True
    log_retention_days: int = 30
    log_llm_verbose: bool = True

    llm_active_provider: str = ""
    llm_save_token_mode: bool = False
    llm_skip_fixture_tutor: bool = True
    llm_request_timeout_sec: float = 30.0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_log_level(self) -> str:
        """Return explicit LOG_LEVEL or derive from LOG_MODE."""
        if self.log_level:
            return self.log_level.upper()
        if self.log_mode == "debug":
            return "DEBUG"
        return "INFO"


settings = Settings()
