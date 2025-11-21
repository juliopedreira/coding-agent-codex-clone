from __future__ import annotations

import logging
from typing import Optional

import typer

from codex.agent.runner import run_prompt
from codex.config import get_settings
from codex.logging import setup_json_logging

app = typer.Typer(
    help="Codex-like CLI powered by LangGraph + LangChain.", invoke_without_command=True
)


def _run_prompt(prompt: str) -> None:
    """Shared prompt execution placeholder."""
    settings = get_settings()
    typer.echo(f"[codex] Running prompt with model={settings.model}")
    typer.echo(f"[codex] prompt: {prompt}")
    result = run_prompt(prompt, settings)
    typer.echo("[codex] analysis -> " + result["analysis"])
    typer.echo("[codex] summary  -> " + result["summary"])


def _interactive_console() -> None:
    """Simple interactive console similar to original Codex."""
    typer.echo("[codex] Interactive console. Type 'exit' or Ctrl-D to quit.")
    while True:
        try:
            prompt = typer.prompt("codex> ")
        except EOFError:
            typer.echo()
            break
        if not prompt.strip():
            continue
        if prompt.strip().lower() in {"exit", "quit"}:
            break
        _run_prompt(prompt)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging."),
) -> Optional[None]:
    level = "DEBUG" if verbose else "INFO"
    setup_json_logging(level=logging.DEBUG if verbose else logging.INFO)
    typer.echo(f"[codex] starting with log level={level}")
    # If no subcommand, enter interactive console.
    if ctx.invoked_subcommand is None:
        _interactive_console()
        ctx.exit()
    return None


@app.command()
def run(prompt: str = typer.Argument(..., help="User prompt to run through the agent")) -> None:
    """Run a single prompt through the agent (placeholder)."""
    _run_prompt(prompt)


@app.command("workflow")
def workflow_run(
    path: str = typer.Argument(..., help="Path to a YAML/JSON workflow definition"),
) -> None:
    """Execute a workflow definition (placeholder)."""
    typer.echo(f"[codex] Executing workflow at {path}")
    typer.echo("[codex] TODO: compile workflow to LangGraph and run.")


@app.command("tools")
def tools_list() -> None:
    """List available tools (placeholder)."""
    typer.echo("[codex] Available tools will be listed here (stub).")


def _main() -> None:
    app()


if __name__ == "__main__":
    _main()
