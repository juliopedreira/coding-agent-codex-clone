from typer.testing import CliRunner

from codax.cli import app

runner = CliRunner()


def test_run_command_executes() -> None:
    result = runner.invoke(app, ["run", "hello world"])
    assert result.exit_code == 0
    assert "Running prompt" not in result.stdout  # new output format
    assert "summary" in result.stdout


def test_workflow_command_executes(tmp_path) -> None:
    wf = tmp_path / "workflow.yaml"
    wf.write_text("steps: []", encoding="utf-8")
    result = runner.invoke(app, ["workflow", str(wf)])
    assert result.exit_code == 0
    assert "workflow success" in result.stdout


def test_workflow_command_accepts_extra_param(tmp_path) -> None:
    wf = tmp_path / "workflow.yaml"
    wf.write_text(
        """
steps:
  - id: write
    tool: fs_write
    args:
      path: out.txt
      content: "{{FEATURE}}"
        """.strip(),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["workflow", str(wf), "--FEATURE=hello-world"])
    assert result.exit_code == 0
    assert (tmp_path / "out.txt").read_text(encoding="utf-8") == "hello-world"


def test_tools_list_command() -> None:
    result = runner.invoke(app, ["tools"])
    assert result.exit_code == 0
    assert "Available tools" in result.stdout


def test_interactive_console_runs() -> None:
    result = runner.invoke(app, [], input="hello\nexit\n")
    assert result.exit_code == 0
    assert "Interactive console" in result.stdout
    assert "summary" in result.stdout


def test_interactive_console_model_command() -> None:
    result = runner.invoke(app, [], input="/model test-model\nhello\nexit\n")
    assert result.exit_code == 0
    assert "model set to test-model" in result.stdout


def test_interactive_console_reason_command() -> None:
    result = runner.invoke(app, [], input="/reason high\nhello\nexit\n")
    assert result.exit_code == 0
    assert "reasoning set to high" in result.stdout


def test_interactive_console_unknown_command() -> None:
    result = runner.invoke(app, [], input="/unknown\nexit\n")
    assert result.exit_code == 0
    assert "unknown command" in result.stdout
