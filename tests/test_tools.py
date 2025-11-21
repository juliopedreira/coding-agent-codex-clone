import sys

from codex.tools.base import Tool, ToolResult
from codex.tools.shell import ShellTool


class EchoTool(Tool):
    name = "echo"
    description = "Echo input"

    def run(self, text: str) -> ToolResult:  # type: ignore[override]
        return ToolResult(output=text, success=True)


def test_tool_base_subclass_runs() -> None:
    tool = EchoTool()
    result = tool.run("hi")
    assert result.output == "hi"
    assert result.success


def test_shell_tool_executes_command(tmp_path) -> None:
    tool = ShellTool(timeout=5)
    msg = "hello-shell"
    result = tool.run(f'"{sys.executable}" -c "print(\'{msg}\')"', cwd=str(tmp_path))
    assert result.success
    assert msg in result.output


def test_shell_tool_timeout(tmp_path) -> None:
    tool = ShellTool(timeout=1)
    # Use python sleep for cross-platform
    result = tool.run(f'"{sys.executable}" -c "import time; time.sleep(2)"', cwd=str(tmp_path))
    assert not result.success
    assert "timed out" in result.output or "Timeout" in result.output
