from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, cast

try:  # CEL is optional; we fall back to simple lookups when missing.
    from cel import evaluate as cel_evaluate
except Exception:  # pragma: no cover - optional runtime dependency
    cel_evaluate = None  # type: ignore[assignment]

from codax.tools.base import Tool, ToolResult
from codax.tools.filesystem import _ensure_workspace


def _load_workflow(path: Path) -> Dict[str, Any]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ModuleNotFoundError as exc:  # pragma: no cover - optional dep
            raise RuntimeError("pyyaml is required for YAML workflows") from exc
        return cast(Dict[str, Any], yaml.safe_load(path.read_text()) or {})
    content = path.read_text()
    return cast(Dict[str, Any], json.loads(content))


def _resolve_path(expr: str, context: Dict[str, Any]) -> Any:
    """Resolve dotted / indexed expressions against the context dict."""

    current: Any = context
    # Split on dots but keep bracketed keys intact.
    tokens = re.split(r"\.(?![^\[]*\])", expr)
    for token in tokens:
        # Handle bracket access: ["key"] or ['key']
        bracket_match = re.match(r"(.+)?\[(?:'|\")([^\]]+)(?:'|\")\]", token)
        if bracket_match:
            head, key = bracket_match.groups()
            if head:
                current = getattr(current, head, current.get(head) if isinstance(current, dict) else None)  # type: ignore[arg-type]
            if isinstance(current, dict):
                current = current.get(key)
            else:
                current = getattr(current, key, None)
            continue
        if isinstance(current, dict):
            current = current.get(token)
        else:
            current = getattr(current, token, None)
    return current


def _eval_expr(expr: str, context: Dict[str, Any]) -> Any:
    # Prefer CEL if available so expressions like steps["Failing"].output work.
    if cel_evaluate is not None:
        try:
            return cel_evaluate(expr, context)
        except Exception:
            # Fall back to simple resolution if CEL parsing fails.
            pass
    # Simple lookup or dotted path resolution
    if expr in context:
        return context.get(expr)
    return _resolve_path(expr, context)


def _render_value(value: Any, context: Dict[str, Any]) -> Any:
    """Render a value by interpolating any {{expr}} segments recursively."""

    if isinstance(value, dict):
        return {k: _render_value(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [_render_value(item, context) for item in value]
    if isinstance(value, str):
        def repl(match: re.Match[str]) -> str:
            expr = match.group(1)
            resolved = _eval_expr(expr, context)
            return "" if resolved is None else str(resolved)

        return re.sub(r"\{\{\s*([^}]+?)\s*\}\}", repl, value)
    return value


@dataclass
class StepRecord:
    output: Any
    metadata: Dict[str, Any] | None
    success: bool


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
        return {key: _render_value(val, context) for key, val in args.items()}

    def _should_skip(self, condition: Any, context: Dict[str, Any]) -> bool:
        if condition is None:
            return False
        # A condition can be a literal bool or an expression string.
        if isinstance(condition, str):
            value = _eval_expr(condition, context)
        else:
            value = _render_value(condition, context)
        return not bool(value)

    def _run_step(
        self,
        step: Dict[str, Any],
        registry: Dict[str, Tool],
        context: Dict[str, Any],
        transcripts: list[str],
    ) -> ToolResult:
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

        retries = int(step.get("retries", 0))
        attempt = 0
        last_result: ToolResult | None = None
        allow_failure = bool(step.get("allow_failure", False))
        while attempt <= retries:
            attempt += 1
            result = tool.run(**rendered_args)
            last_result = result
            transcripts.append(f"{step_id}:{tool_name}:{result.output}")
            if result.success:
                break
        if not last_result or not last_result.success:
            if not allow_failure:
                return ToolResult(
                    output=f"step {step_id} failed: {last_result.output if last_result else 'unknown'}",
                    success=False,
                    metadata={"step": step_id, "transcript": transcripts},
                )
            # Preserve failure output but mark as allowed so execution continues.
            last_result = ToolResult(
                output=last_result.output if last_result else "unknown",  # type: ignore[union-attr]
                success=True,
                metadata={
                    **(last_result.metadata or {}),  # type: ignore[union-attr]
                    "allowed_failure": True,
                    "step": step_id,
                },
            )

        if assign := step.get("assign"):
            context[assign] = last_result.output
        # Always capture step output for rich templating.
        step_record = StepRecord(output=last_result.output, metadata=last_result.metadata, success=last_result.success)
        steps_map = context.setdefault("steps", {})
        steps_map[step_id] = step_record
        # convenience access e.g. {{FailingTest.output}}
        context[step_id] = step_record.output
        return last_result

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
        context.setdefault("steps", {})
        transcripts: list[str] = []
        for step in steps:
            condition = step.get("when")
            if self._should_skip(condition, context):
                transcripts.append(f"{step.get('id','unknown')}:skipped")
                continue

            if "loop" in step and isinstance(step["loop"], list):
                loop_var = step.get("loop_var", "item")
                for item in step["loop"]:
                    context[loop_var] = item
                    result = self._run_step(step, registry, context, transcripts)
                    if not result.success:
                        return result
                continue

            result = self._run_step(step, registry, context, transcripts)
            if not result.success:
                return result

        return ToolResult(
            output="workflow completed",
            success=True,
            metadata={"transcript": transcripts, "params": params or {}, "context": context},
        )
