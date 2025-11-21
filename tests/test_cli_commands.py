from typer.testing import CliRunner

from codex.cli import app

runner = CliRunner()


def test_run_command_executes() -> None:
    result = runner.invoke(app, ["run", "hello world"])
    assert result.exit_code == 0
    assert "Running prompt" in result.stdout


def test_workflow_command_executes(tmp_path) -> None:
    wf = tmp_path / "workflow.yaml"
    wf.write_text("steps: []", encoding="utf-8")
    result = runner.invoke(app, ["workflow", str(wf)])
    assert result.exit_code == 0
    assert "Executing workflow" in result.stdout


def test_tools_list_command() -> None:
    result = runner.invoke(app, ["tools"])
    assert result.exit_code == 0
    assert "Available tools" in result.stdout


def test_interactive_console_runs() -> None:
    result = runner.invoke(app, [], input="hello\nexit\n")
    assert result.exit_code == 0
    assert "Interactive console" in result.stdout
    assert "Running prompt" in result.stdout
