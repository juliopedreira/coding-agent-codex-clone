from typer.testing import CliRunner

from codex.cli import app

runner = CliRunner()


def test_run_command_executes() -> None:
    result = runner.invoke(app, ["run", "hello world"])
    assert result.exit_code == 0
    assert "Running prompt" in result.stdout
    assert "analysis" in result.stdout
    assert "summary" in result.stdout


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
    assert "summary" in result.stdout


def test_interactive_console_model_command() -> None:
    result = runner.invoke(app, [], input="/model test-model\n/model x\nhello\nexit\n")
    assert result.exit_code == 0
    assert "model set to x" in result.stdout
    assert "Running prompt with model=x" in result.stdout


def test_interactive_console_reason_command() -> None:
    result = runner.invoke(app, [], input="/reason high\nhello\nexit\n")
    assert result.exit_code == 0
    assert "reasoning set to high" in result.stdout
    assert "reasoning effort=high" in result.stdout


def test_interactive_console_unknown_command() -> None:
    result = runner.invoke(app, [], input="/unknown\nexit\n")
    assert result.exit_code == 0
    assert "unknown command" in result.stdout
