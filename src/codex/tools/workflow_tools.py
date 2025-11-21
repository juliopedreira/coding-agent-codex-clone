from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, cast

from codex.tools.base import Tool, ToolResult
from codex.tools.filesystem import _ensure_workspace


def _load_workflow(path: Path) -> Dict[str, Any]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ModuleNotFoundError as exc:
            raise RuntimeError("pyyaml is required for YAML workflows") from exc
        return yaml.safe_load(path.read_text()) or {}
    content = path.read_text()
    return cast(Dict[str, Any], json.loads(content))


class WorkflowValidateTool(Tool):
    name = "workflow_validate"
    description = "Validate workflow file against schema v1."

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def run(self, path: str) -> ToolResult:
        target = _ensure_workspace(Path(path), self.workspace_root)
        if not target.exists():
            return ToolResult(output="workflow file not found", success=False, metadata=None)
        try:
            payload = _load_workflow(target)
        except Exception as exc:  # noqa: BLE001
            return ToolResult(output=str(exc), success=False, metadata=None)

        if not isinstance(payload, dict) or "steps" not in payload:
            return ToolResult(output="workflow missing 'steps'", success=False, metadata=None)
        steps = payload.get("steps")
        if not isinstance(steps, list):
            return ToolResult(output="'steps' must be a list", success=False, metadata=None)
        return ToolResult(
            output="valid",
            success=True,
            metadata={"step_count": len(steps)},
        )


class WorkflowRunTool(Tool):
    name = "workflow_run"
    description = "Execute a workflow definition using the tool registry."

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root
        self.validator = WorkflowValidateTool(workspace_root)

    def _render_args(self, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        def render(value: Any) -> Any:
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                key = value.strip("{} ").replace(" ", "")
                return context.get(key, "")
            return value

        return {key: render(val) for key, val in args.items()}

    def run(
        self,
        path: str,
        params: Dict[str, str] | None = None,
        registry: Dict[str, Tool] | None = None,
    ) -> ToolResult:
        validation = self.validator.run(path)
        if not validation.success:
            return validation
        if registry is None:
            return ToolResult(
                output="registry is required to execute workflow",
                success=False,
                metadata=None,
            )

        workflow = _load_workflow(_ensure_workspace(Path(path), self.workspace_root))
        steps = workflow.get("steps", [])
        context: Dict[str, Any] = dict(params or {})
        transcripts: list[str] = []
        for step in steps:
            step_id = step.get("id", "unknown")
            tool_name = step.get("tool")
            if not tool_name or tool_name not in registry:
                return ToolResult(
                    output=f"step {step_id} references unknown tool '{tool_name}'",
                    success=False,
                    metadata={"step": step_id},
                )
            tool = registry[tool_name]
            raw_args: Dict[str, Any] = step.get("args", {})
            rendered_args = self._render_args(raw_args, context)
            result = tool.run(**rendered_args)
            transcripts.append(f"{step_id}:{tool_name}:{result.output}")
            if not result.success:
                return ToolResult(
                    output=f"step {step_id} failed: {result.output}",
                    success=False,
                    metadata={"step": step_id, "transcript": transcripts},
                )
            if assign := step.get("assign"):
                context[assign] = result.output

        return ToolResult(
            output="workflow completed",
            success=True,
            metadata={"transcript": transcripts, "params": params or {}, "context": context},
        )
