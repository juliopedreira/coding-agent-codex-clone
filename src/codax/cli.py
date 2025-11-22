from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import typer

from codax.agent.runner import create_agent_graph, run_prompt
from codax.config import SafetyMode, get_settings, persist_settings
from codax.logging import RunContext, setup_json_logging
from codax.tools import build_tool_registry
from codax.workflows.compiler import load_and_compile

app = typer.Typer(help="Codax CLI powered by LangGraph-like planner/executor.")


def _render_stream(stream) -> None:
    for event in stream:
        if event.get("type") == "token":
            typer.echo(event["text"], nl=False)
    typer.echo()


def _run_prompt(prompt: str, model: str | None = None, reasoning: str | None = None) -> None:
    """Execute prompt through the agent graph."""
    settings = get_settings()
    if model:
        settings.model = model
    result = run_prompt(prompt, settings, model_override=model, reasoning=reasoning)
    typer.echo(f"[codax] model={result['model']} reasoning={result['reasoning']}")
    typer.echo(f"[codax] analysis -> {result['analysis']}")
    typer.echo(f"[codax] summary  -> {result['summary']}")


def _interactive_console() -> None:
    """Interactive console with slash commands."""
    typer.echo("[codax] Interactive console. Type 'exit' or Ctrl-D to quit.")
    settings = get_settings()
    current_model = settings.model
    current_reasoning = settings.reasoning_effort
    safety_mode = settings.safety_mode
    search_backend = settings.search_backend
    typer.echo(f"[codax] model={current_model} safety={safety_mode} search={search_backend}")
    typer.echo("Commands: /model <name>, /reason <effort>, /safety <mode>, /search_backend <name>, /save, /help")
    graph = create_agent_graph(settings)
    while True:
        try:
            prompt = typer.prompt("codax> ")
        except EOFError:
            typer.echo()
            break
        if not prompt.strip():
            continue
        if prompt.strip().lower() in {"exit", "quit"}:
            break
        if prompt.startswith("/"):
            tokens = prompt.strip().split()
            cmd = tokens[0][1:]
            if cmd == "model" and len(tokens) >= 2:
                current_model = tokens[1]
                settings.model = current_model
                typer.echo(f"[codax] model set to {current_model}")
                continue
            if cmd in {"reason", "reasoning"} and len(tokens) >= 2:
                current_reasoning = tokens[1]
                settings.reasoning_effort = current_reasoning
                typer.echo(f"[codax] reasoning set to {current_reasoning}")
                continue
            if cmd == "safety" and len(tokens) >= 2:
                safety_mode = tokens[1]
                settings.safety_mode = safety_mode
                typer.echo(f"[codax] safety set to {safety_mode}")
                continue
            if cmd == "search_backend" and len(tokens) >= 2:
                search_backend = tokens[1]
                settings.search_backend = search_backend
                typer.echo(f"[codax] search backend set to {search_backend}")
                continue
            if cmd == "save":
                path = persist_settings(settings)
                typer.echo(f"[codax] settings persisted to {path}")
                continue
            if cmd in {"help", "h"}:
                typer.echo("Use /model, /reason, /safety, /search_backend, /save, exit to quit.")
                continue
            typer.echo(f"[codax] unknown command '{cmd}'")
            continue
        result = graph.run(prompt, reasoning=current_reasoning)
        typer.echo(f"summary: {result['summary']}")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging."),
) -> Optional[None]:
    level = logging.DEBUG if verbose else logging.INFO
    run_ctx = RunContext(run_id="console")
    setup_json_logging(level=level, run=run_ctx)
    if ctx.invoked_subcommand is None:
        _interactive_console()
        ctx.exit()
    return None


@app.command()
def run(
    prompt: str = typer.Argument(..., help="User prompt to run through the agent"),
    model: str | None = typer.Option(None, "--model", "-m", help="Override model name"),
    reasoning: str | None = typer.Option(None, "--reasoning", "-r", help="Override reasoning effort"),
) -> None:
    """Run a single prompt through the agent."""
    _run_prompt(prompt, model=model, reasoning=reasoning)


def _parse_extra_params(args: list[str]) -> dict[str, str]:
    """Parse unknown CLI args of form --KEY=value or --KEY value."""

    params: dict[str, str] = {}
    i = 0
    while i < len(args):
        token = args[i]
        if token.startswith("--"):
            keyval = token[2:]
            value: str
            if "=" in keyval:
                key, value = keyval.split("=", 1)
            else:
                key = keyval
                value = "true"
                if i + 1 < len(args) and not args[i + 1].startswith("-"):
                    value = args[i + 1]
                    i += 1
            params[key] = value
        i += 1
    return params


@app.command(
    "workflow",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def workflow_run(
    ctx: typer.Context,
    path: str = typer.Argument(..., help="Path to a YAML/JSON workflow definition"),
    param: list[str] | None = typer.Option(None, "--param", "-p", help="key=value parameters"),
) -> None:
    """Execute a workflow definition."""
    settings = get_settings()
    path_obj = Path(path).expanduser().resolve()
    # Prefer the repository root (detected via .git) so workflows under examples/ can
    # still modify project files safely. Fallback to the workflow's parent directory.
    candidate = path_obj.parent
    git_root = next((p for p in (candidate,) + tuple(candidate.parents) if (p / ".git").exists()), None)
    settings.workspace_root = git_root or candidate
    kv_params: dict[str, str] = _parse_extra_params(list(ctx.args))
    for item in param or []:
        if "=" in item:
            key, val = item.split("=", 1)
            kv_params[key] = val
    compiled = load_and_compile(path, settings=settings)
    result = compiled.run(params=kv_params)
    typer.echo(f"[codax] workflow success={result['success']}")
    if result["metadata"]:
        typer.echo(result["metadata"])


@app.command("tools")
def tools_list() -> None:
    """List available tools."""
    registry = build_tool_registry(get_settings())
    typer.echo("[codax] Available tools:")
    for name, tool in sorted(registry.items()):
        typer.echo(f"- {name}: {getattr(tool, 'description', '')}")

@app.command("tool-run")
def tool_run(
    tool: str = typer.Argument(..., help="Tool name to invoke"),
    args: str = typer.Argument("{}", help="JSON object with tool arguments"),
) -> None:
    """
    Invoke any registered tool directly (bypassing the LLM).

    Example:
    poetry run codax tool-run update_plan '{"plan":[{"step":"one","status":"pending"}],"explanation":"demo"}'
    """
    import json

    registry = build_tool_registry(get_settings())
    if tool not in registry:
        typer.echo(f"[codax] unknown tool '{tool}'")
        raise typer.Exit(code=1)
    try:
        payload = json.loads(args)
    except json.JSONDecodeError as exc:
        typer.echo(f"[codax] invalid JSON args: {exc}")
        raise typer.Exit(code=1)
    runner = registry[tool]
    result = runner.run(**payload)  # type: ignore[arg-type]
    typer.echo(json.dumps({"output": result.output, "success": result.success, "metadata": result.metadata}, indent=2))


@app.command("logs")
def logs_tail() -> None:
    """Tail log file path."""
    settings = get_settings()
    log_path = settings.logs_dir / "codax.log"
    typer.echo(str(log_path))


@app.command("config")
def config_show() -> None:
    """Show resolved configuration."""
    settings = get_settings()
    typer.echo(settings.model_dump_json(indent=2))


def _main() -> None:
    app()


if __name__ == "__main__":
    _main()
