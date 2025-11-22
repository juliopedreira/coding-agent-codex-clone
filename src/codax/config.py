from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Tuple

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict


DEFAULT_DATA_DIR = Path("~/.codax").expanduser()
DEFAULT_CONFIG_FILE = DEFAULT_DATA_DIR / "config.toml"
DEFAULT_LOG_DIR = DEFAULT_DATA_DIR / "logs"


class SafetyMode(str):
    SAFE = "safe"
    ON_REQUEST = "on-request"
    OFF = "off"


class Settings(BaseSettings):
    """
    Runtime configuration for the Codax CLI.

    The settings sources are, in order of precedence:
    1. Explicit init arguments
    2. TOML config file (default: ~/.codax/config.toml)
    3. Environment variables
    4. Defaults declared below
    """

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core
    openai_api_key: str | None = Field(default=None)
    model: str = Field(default="gpt-4o-mini")
    reasoning_effort: str | None = Field(default=None)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    request_timeout_seconds: int = Field(default=60, ge=1)
    # Safety & runtime toggles
    safety_mode: str = Field(default=SafetyMode.ON_REQUEST)
    search_backend: str = Field(default="ddg")
    allow_network: bool = Field(default=True)
    allow_git_commits: bool = Field(default=False)
    # Paths
    workspace_root: Path = Field(default_factory=lambda: Path.cwd())
    data_dir: Path = Field(default=DEFAULT_DATA_DIR)
    config_file: Path = Field(default=DEFAULT_CONFIG_FILE)
    logs_dir: Path = Field(default=DEFAULT_LOG_DIR)
    log_max_bytes: int = Field(default=5 * 1024 * 1024)
    log_backup_count: int = Field(default=3)

    @field_validator("workspace_root", "data_dir", "config_file", "logs_dir", mode="before")
    @classmethod
    def _expand_paths(cls, value: str | Path) -> Path:
        return Path(value).expanduser().resolve()

    @field_validator("safety_mode")
    @classmethod
    def _validate_safety(cls, value: str) -> str:
        allowed = {SafetyMode.SAFE, SafetyMode.ON_REQUEST, SafetyMode.OFF}
        if value not in allowed:
            raise ValueError(f"safety_mode must be one of {allowed}")
        return value

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        # Insert TOML config between init args and env vars.
        config_path = getattr(init_settings, "init_kwargs", {}).get("config_file", DEFAULT_CONFIG_FILE)
        return (
            init_settings,
            TomlConfigSource(settings_cls, config_path=config_path),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )

    def ensure_directories(self) -> None:
        """Create data/log directories if missing."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        # Ensure config file parent exists; file is optional.
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

    def to_toml(self) -> str:
        payload: Dict[str, Any] = {
            "openai_api_key": self.openai_api_key,
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "temperature": self.temperature,
            "request_timeout_seconds": self.request_timeout_seconds,
            "safety_mode": self.safety_mode,
            "search_backend": self.search_backend,
            "allow_network": self.allow_network,
            "allow_git_commits": self.allow_git_commits,
            "workspace_root": str(self.workspace_root),
            "data_dir": str(self.data_dir),
            "config_file": str(self.config_file),
            "logs_dir": str(self.logs_dir),
            "log_max_bytes": self.log_max_bytes,
            "log_backup_count": self.log_backup_count,
        }
        lines = ["[codax]"]
        for key, value in payload.items():
            if value is None:
                continue
            toml_value = f'"{value}"' if isinstance(value, str) else value
            lines.append(f"{key} = {toml_value}")
        return "\n".join(lines) + "\n"


class TomlConfigSource(PydanticBaseSettingsSource):
    """Custom settings source that reads a TOML config file."""

    def __init__(self, settings_cls: type[BaseSettings], config_path: Path | None = None) -> None:
        super().__init__(settings_cls)
        self._data: Dict[str, Any] | None = None
        self.config_path = (config_path or DEFAULT_CONFIG_FILE).expanduser().resolve()

    def _load(self) -> Dict[str, Any]:
        if self._data is not None:
            return self._data
        data: Dict[str, Any] = {}
        config_path = self.config_path
        if not config_path.exists():
            self._data = {}
            return self._data
        try:
            with config_path.open("rb") as handle:
                loaded = tomllib.load(handle)
            section = loaded.get("codax", loaded)
            data = dict(section)
        except Exception:
            data = {}
        self._data = data
        return data

    def __call__(self) -> Dict[str, Any]:
        return self._load()

    def get_field_value(self, field, field_name: str) -> tuple[Any, str | None, bool]:
        data = self._load()
        if field_name in data:
            return data[field_name], field_name, True
        return None, field_name, False

    def prepare_field(self, field):
        return field


def persist_settings(settings: Settings, path: Path | None = None) -> Path:
    """Persist current settings to TOML."""
    target = path or settings.config_file
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(settings.to_toml(), encoding="utf-8")
    return target


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings
