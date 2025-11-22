from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from codax.tools import build_tool_registry
from codax.tools.workflow_tools import WorkflowRunTool, _load_workflow
from codax.config import Settings


def load_workflow(path: str | Path) -> Dict[str, Any]:
    """
    Load and validate a workflow definition from YAML/JSON.
    """
    wf_path = Path(path)
    if not wf_path.exists():
        raise FileNotFoundError(path)
    return _load_workflow(wf_path)


@dataclass
class CompiledWorkflow:
    definition: Dict[str, Any]
    settings: Settings

    def run(self, params: Dict[str, str] | None = None) -> Dict[str, Any]:
        registry = build_tool_registry(self.settings)
        runner = WorkflowRunTool(self.settings.workspace_root)
        result = runner.run(
            path=self.definition.get("__source__", ""),
            params=params or {},
            registry=registry,  # type: ignore[arg-type]
        )
        return {
            "success": result.success,
            "output": result.output,
            "metadata": result.metadata,
        }


def compile_workflow(definition: Dict[str, Any]) -> CompiledWorkflow:
    """
    Compile workflow definition into a simple runnable wrapper.
    """
    settings = definition.get("__settings__")
    if not isinstance(settings, Settings):
        settings = Settings()
    # Preserve source path if present.
    return CompiledWorkflow(definition=definition, settings=settings)


def load_and_compile(path: str | Path, settings: Settings | None = None) -> CompiledWorkflow:
    wf = load_workflow(path)
    source_path = Path(path).resolve()
    if settings is None:
        settings = Settings(workspace_root=source_path.parent)
    else:
        # Respect explicitly provided workspace_root; only fill when unset.
        if settings.workspace_root is None:
            settings.workspace_root = source_path.parent
    wf["__source__"] = str(Path(path).resolve())
    wf["__settings__"] = settings
    return compile_workflow(wf)
