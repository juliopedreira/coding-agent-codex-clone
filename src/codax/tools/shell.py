from __future__ import annotations

import shlex
import subprocess
from typing import List

from codax.safety import ActionType, SafetyPolicy, guard_action
from codax.tools.base import Tool, ToolResult

RISKY_TOKENS = {"rm", "rm -rf", "mkfs", ":(){", "shutdown", "reboot", "dd ", "chmod 777", "chown"}


class ShellTool(Tool):
    name = "shell"
    description = "Execute shell commands in the workspace."

    def __init__(
        self,
        policy: SafetyPolicy,
        allowed_commands: List[str] | None = None,
        timeout: int = 60,
    ) -> None:
        self.policy = policy
        self.allowed_commands = allowed_commands
        self.timeout = timeout

    def _is_risky(self, command: str) -> bool:
        return any(token in command for token in RISKY_TOKENS)

    def run(self, command: str, cwd: str | None = None, timeout: int | None = None) -> ToolResult:
        # allow-list enforcement
        if self.allowed_commands is not None:
            head = shlex.split(command)[0] if command.strip() else ""
            if head not in self.allowed_commands:
                return ToolResult(
                    output=f"Command '{head}' is not in the allowed list.",
                    success=False,
                    metadata={"returncode": None},
                )

        detail = f"shell command: {command}"
        safety_result = guard_action(self.policy, ActionType.SHELL, detail)
        if safety_result:
            return safety_result

        warning = ""
        if self._is_risky(command):
            warning = "[warning] risky command detected; proceed with caution.\n"

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
            output = (result.stdout or "") + (result.stderr or "")
            success = result.returncode == 0
            if len(output) > 4000:
                output = output[:4000] + "\n[truncated]"
            return ToolResult(
                output=warning + output,
                success=success,
                metadata={"returncode": result.returncode, "cwd": cwd},
            )
        except subprocess.TimeoutExpired as exc:
            return ToolResult(output=str(exc), success=False, metadata={"returncode": None})
