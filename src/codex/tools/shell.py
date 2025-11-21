from __future__ import annotations

import subprocess
from typing import List

from codex.tools.base import Tool, ToolResult


class ShellTool(Tool):
    name = "shell"
    description = "Execute shell commands in the workspace."

    def __init__(self, allowed_commands: List[str] | None = None, timeout: int = 60) -> None:
        self.allowed_commands = allowed_commands
        self.timeout = timeout

    def run(self, command: str, cwd: str | None = None) -> ToolResult:
        # Stub implementation; real version will enforce allowlists and streaming.
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                timeout=self.timeout,
                text=True,
            )
            output = result.stdout + result.stderr
            success = result.returncode == 0
            return ToolResult(
                output=output, success=success, metadata={"returncode": result.returncode}
            )
        except subprocess.TimeoutExpired as exc:
            return ToolResult(output=str(exc), success=False, metadata={"returncode": None})
