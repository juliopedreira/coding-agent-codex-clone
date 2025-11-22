from __future__ import annotations

import json
import logging
import logging.handlers
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from codax.config import Settings


@dataclass
class RunContext:
    run_id: str
    session_id: str | None = None


class SecretRedactor(logging.Filter):
    """Filter that redacts known secrets in log messages."""

    def __init__(self, secrets: Iterable[str]) -> None:
        super().__init__()
        self.secrets = [s for s in secrets if s]

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        message = record.getMessage()
        for secret in self.secrets:
            if secret and secret in message:
                message = message.replace(secret, "***REDACTED***")
        record.msg = message
        record.args = ()
        return True


class JsonFormatter(logging.Formatter):
    def __init__(self, run: RunContext | None = None) -> None:
        super().__init__()
        self.run = run

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if self.run:
            payload["run_id"] = self.run.run_id
            if self.run.session_id:
                payload["session_id"] = self.run.session_id
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        if record.extra if hasattr(record, "extra") else None:  # type: ignore[attr-defined]
            payload["extra"] = record.extra  # type: ignore[attr-defined]
        return json.dumps(payload)


def setup_json_logging(
    level: int = logging.INFO,
    settings: Optional[Settings] = None,
    run: RunContext | None = None,
    mirror_stdout: bool = True,
) -> Optional[str]:
    """
    Configure JSON logging.

    - Always logs to stdout when `mirror_stdout` is True.
    - If settings provided, also logs to rotating file under settings.logs_dir.
    Returns log file path if configured.
    """
    handlers: list[logging.Handler] = []

    formatter = JsonFormatter(run)
    redactor = SecretRedactor(
        [settings.openai_api_key] if settings and settings.openai_api_key else []
    )

    if mirror_stdout:
        stream_handler = logging.StreamHandler(stream=sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler.addFilter(redactor)
        handlers.append(stream_handler)

    log_path: str | None = None
    if settings:
        settings.ensure_directories()
        log_path = str(settings.logs_dir / "codax.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=settings.log_max_bytes,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(redactor)
        handlers.append(file_handler)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    for handler in handlers:
        root.addHandler(handler)
    root.propagate = False
    return log_path
