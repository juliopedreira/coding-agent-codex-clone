from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Runtime configuration for the Codex clone."""

    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    model: str = Field(default="gpt-4o")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    workspace_root: Path = Field(default_factory=lambda: Path.cwd())
    request_timeout_seconds: int = Field(default=60, ge=1)
    allow_network: bool = Field(default=True)
    safety_confirm_destructive: bool = Field(default=True)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("workspace_root", pre=True)
    def _expand_workspace(cls, value: str | Path) -> Path:
        path = Path(value).expanduser().resolve()
        return path


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
