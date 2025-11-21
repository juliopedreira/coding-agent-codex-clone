from __future__ import annotations

import shlex
import subprocess
from typing import List

from codex.tools.base import Tool, ToolResult


class ShellTool(Tool):
    name = "shell"
    description = "Execute shell commands in the workspace."

    def __init__(self, allowed_commands: List[str] | None = None, timeout: int = 60) -> None:
        self.allowed_commands = allowed_commands
        self.timeout = timeout

    def _is_risky(self, command: str) -> bool:
        risky_tokens = {"rm", "rm -rf", "mkfs", ":(){", "shutdown", "reboot"}
        return any(token in command for token in risky_tokens)

    def run(self, command: str, cwd: str | None = None, timeout: int | None = None) -> ToolResult:
        if self.allowed_commands is not None:
            head = shlex.split(command)[0] if command.strip() else ""
            if head not in self.allowed_commands:
                return ToolResult(
                    output=f"Command '{head}' is not in the allowed list.",
                    success=False,
                    metadata={"returncode": None},
                )

        if self._is_risky(command):
            # Non-blocking warning embedded in output for now.
            warning = "[warning] risky command detected; proceed with caution.\n"
        else:
            warning = ""

        try:
            effective_timeout = timeout or self.timeout
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                timeout=effective_timeout,
                text=True,
            )
            output = result.stdout + result.stderr
            success = result.returncode == 0
            return ToolResult(
                output=warning + output,
                success=success,
                metadata={"returncode": result.returncode},
            )
        except subprocess.TimeoutExpired as exc:
            return ToolResult(output=str(exc), success=False, metadata={"returncode": None})
