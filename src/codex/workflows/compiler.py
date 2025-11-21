from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def load_workflow(path: str | Path) -> Dict[str, Any]:
    """Stub to load and validate a workflow definition."""
    _ = path
    raise NotImplementedError("Workflow loading not implemented yet.")


def compile_workflow(definition: Dict[str, Any]) -> Any:
    """Stub to compile workflow definition into a LangGraph graph."""
    _ = definition
    raise NotImplementedError("Workflow compilation not implemented yet.")
