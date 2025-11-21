from typer.testing import CliRunner

from codex.cli import app


runner = CliRunner()


def test_cli_runs_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "codex" in result.stdout.lower()
