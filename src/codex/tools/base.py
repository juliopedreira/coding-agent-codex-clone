from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ToolResult:
    output: str
    success: bool
    metadata: Dict[str, Any] | None = None


class Tool(ABC):
    """Abstract tool interface mirroring Codex expectations."""

    name: str
    description: str

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> ToolResult:
        """Execute the tool."""
