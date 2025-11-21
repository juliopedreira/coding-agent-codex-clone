from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Codex clone."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    openai_api_key: str | None = Field(default=None)
    model: str = Field(default="gpt-4o")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    workspace_root: Path = Field(default_factory=lambda: Path.cwd())
    request_timeout_seconds: int = Field(default=60, ge=1)
    allow_network: bool = Field(default=True)
    safety_confirm_destructive: bool = Field(default=True)
    allow_git_commits: bool = Field(default=False)

    @field_validator("workspace_root", mode="before")
    def _expand_workspace(cls, value: str | Path) -> Path:
        path = Path(value).expanduser().resolve()
        return path


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
