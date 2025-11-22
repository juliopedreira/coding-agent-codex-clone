from typer.testing import CliRunner

from codax.cli import app

runner = CliRunner()


def test_cli_runs_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "codax" in result.stdout.lower()
