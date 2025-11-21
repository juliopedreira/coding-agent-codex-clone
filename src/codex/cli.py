from __future__ import annotations

import typer

from codex.config import get_settings
from codex.logging import setup_json_logging

app = typer.Typer(help="Codex-like CLI powered by LangGraph + LangChain.")


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging."),
) -> None:
    level = "DEBUG" if verbose else "INFO"
    setup_json_logging()
    typer.echo(f"[codex] starting with log level={level}")


@app.command()
def run(prompt: str = typer.Argument(..., help="User prompt to run through the agent")) -> None:
    """Run a single prompt through the agent (placeholder)."""
    settings = get_settings()
    typer.echo(f"[codex] Running prompt with model={settings.model}")
    typer.echo(f"[codex] prompt: {prompt}")
    typer.echo("[codex] TODO: wire LangGraph agent execution.")


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
