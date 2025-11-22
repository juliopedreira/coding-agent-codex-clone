from __future__ import annotations

import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

from codax.tools.base import Tool, ToolResult
from codax.tools.filesystem import _ensure_workspace


class ShellCommandTool(Tool):
    name = "shell_command"
    description = "Run a single shell script string in the default shell."

    def __init__(self, workspace_root: Path, timeout: int = 60) -> None:
        self.workspace_root = workspace_root
        self.timeout = timeout

    def run(
        self,
        command: str,
        workdir: str | None = None,
        timeout_ms: int | None = None,
        with_escalated_permissions: bool = False,  # noqa: ARG002
        justification: str | None = None,  # noqa: ARG002
    ) -> ToolResult:
        cwd = _ensure_workspace(Path(workdir or "."), self.workspace_root)
        timeout = (timeout_ms / 1000.0) if timeout_ms else self.timeout
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = (result.stdout or "") + (result.stderr or "")
            return ToolResult(output=output, success=result.returncode == 0, metadata={"returncode": result.returncode})
        except subprocess.TimeoutExpired as exc:  # pragma: no cover
            return ToolResult(output=str(exc), success=False, metadata={"returncode": None})


class ExecCommandTool(Tool):
    name = "exec_command"
    description = "Run a command (pty-like) and return its output."
    _session_counter = 0
    _sessions: dict[int, str] = {}

    def __init__(self, workspace_root: Path, timeout_ms: int = 60000) -> None:
        self.workspace_root = workspace_root
        self.timeout_ms = timeout_ms

    def run(
        self,
        cmd: str,
        workdir: str | None = None,
        shell: str | None = None,  # noqa: ARG002
        login: bool | None = None,  # noqa: ARG002
        yield_time_ms: int | None = None,  # noqa: ARG002
        max_output_tokens: int | None = None,  # noqa: ARG002
        with_escalated_permissions: bool = False,  # noqa: ARG002
        justification: str | None = None,  # noqa: ARG002
    ) -> ToolResult:
        cwd = _ensure_workspace(Path(workdir or "."), self.workspace_root)
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout_ms / 1000.0,
            )
            output = (result.stdout or "") + (result.stderr or "")
            return ToolResult(output=output, success=result.returncode == 0, metadata={"returncode": result.returncode})
        except subprocess.TimeoutExpired as exc:  # pragma: no cover
            return ToolResult(output=str(exc), success=False, metadata={"returncode": None})

    @classmethod
    def create_session(cls, initial_output: str | None = None) -> int:
        cls._session_counter += 1
        cls._sessions[cls._session_counter] = initial_output or ""
        return cls._session_counter


class WriteStdinTool(Tool):
    name = "write_stdin"
    description = "Write characters to an exec session (simplified)."

    def run(
        self,
        session_id: int,
        chars: str | None = None,
        yield_time_ms: int | None = None,  # noqa: ARG002
        max_output_tokens: int | None = None,  # noqa: ARG002
    ) -> ToolResult:
        if session_id not in ExecCommandTool._sessions:
            return ToolResult(output="session not found", success=False, metadata=None)
        log = ExecCommandTool._sessions[session_id]
        if chars:
            log += chars
            ExecCommandTool._sessions[session_id] = log
        return ToolResult(output=log, success=True, metadata={"session_id": session_id})


class ApplyPatchTool(Tool):
    name = "apply_patch"
    description = "Apply a unified diff patch to the workspace."

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def run(self, input: str) -> ToolResult:  # noqa: A003
        # use git apply --check then apply
        repo = self.workspace_root
        try:
            check = subprocess.run(
                ["git", "-C", str(repo), "apply", "--check"],
                input=input,
                text=True,
                capture_output=True,
            )
            if check.returncode != 0:
                return ToolResult(
                    output=(check.stdout or "") + (check.stderr or ""),
                    success=False,
                    metadata={"returncode": check.returncode},
                )
            apply = subprocess.run(
                ["git", "-C", str(repo), "apply"],
                input=input,
                text=True,
                capture_output=True,
            )
            output = (apply.stdout or "") + (apply.stderr or "")
            return ToolResult(output=output, success=apply.returncode == 0, metadata={"returncode": apply.returncode})
        except Exception as exc:  # pragma: no cover
            return ToolResult(output=str(exc), success=False, metadata=None)


class UpdatePlanTool(Tool):
    name = "update_plan"
    description = "Record a planning update."
    _last_plan: list[dict[str, str]] = []
    _lock = threading.Lock()

    def run(self, plan: list[dict[str, str]], explanation: str | None = None) -> ToolResult:
        with self._lock:
            UpdatePlanTool._last_plan = plan
        return ToolResult(
            output="Plan updated",
            success=True,
            metadata={"count": len(plan), "explanation": explanation},
        )


class GrepFilesTool(Tool):
    name = "grep_files"
    description = "Find files whose contents match a pattern."

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def run(
        self,
        pattern: str,
        include: str | None = None,
        path: str | None = None,
        limit: int | None = None,
    ) -> ToolResult:
        search_root = _ensure_workspace(Path(path or "."), self.workspace_root)
        limit = limit or 100
        try:
            if shutil.which("rg"):
                cmd = ["rg", "--files-with-matches", "-n", pattern, str(search_root)]
                if include:
                    cmd.extend(["-g", include])
                proc = subprocess.run(cmd, capture_output=True, text=True)
                lines = proc.stdout.strip().splitlines() if proc.stdout else []
            else:
                lines = []
                for root, _, files in os.walk(search_root):
                    for fname in files:
                        if include and not Path(fname).match(include):
                            continue
                        fpath = Path(root) / fname
                        try:
                            with fpath.open("r", encoding="utf-8") as handle:
                                if re.search(pattern, handle.read()):
                                    lines.append(str(fpath))
                        except Exception:
                            continue
            lines = lines[:limit]
            if not lines:
                return ToolResult(output="no matches", success=False, metadata={"count": 0})
            return ToolResult(output="\n".join(lines), success=True, metadata={"count": len(lines)})
        except Exception as exc:  # pragma: no cover
            return ToolResult(output=str(exc), success=False, metadata=None)


class ReadFileAdvancedTool(Tool):
    name = "read_file"
    description = "Read a file with optional line slicing."

    def run(
        self,
        file_path: str,
        offset: int | None = None,
        limit: int | None = None,
        mode: str | None = None,  # noqa: ARG002
        indentation: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> ToolResult:
        path = Path(file_path)
        if not path.exists():
            return ToolResult(output="file not found", success=False, metadata=None)
        start = max((offset or 1), 1)
        max_lines = limit or 200
        try:
            with path.open("r", encoding="utf-8") as handle:
                lines = handle.readlines()
        except UnicodeDecodeError:
            return ToolResult(output="binary file blocked", success=False, metadata=None)
        slice_lines = lines[start - 1 : start - 1 + max_lines]
        numbered = [f"{i+start}: {line.rstrip()}" for i, line in enumerate(slice_lines)]
        return ToolResult(
            output="\n".join(numbered),
            success=True,
            metadata={"start": start, "returned": len(slice_lines)},
        )


class ListDirAdvancedTool(Tool):
    name = "list_dir"
    description = "List a directory with pagination."

    def run(
        self,
        dir_path: str,
        offset: int | None = None,
        limit: int | None = None,
        depth: int | None = None,
    ) -> ToolResult:
        start = max((offset or 1), 1)
        limit = limit or 100
        max_depth = depth or 1
        base = Path(dir_path)
        if not base.exists():
            return ToolResult(output="dir not found", success=False, metadata=None)
        entries: list[str] = []

        def walk(path: Path, current_depth: int) -> None:
            if current_depth > max_depth or not path.is_dir():
                return
            for entry in sorted(path.iterdir()):
                kind = "dir" if entry.is_dir() else "file"
                entries.append(f"{entry}{'/' if entry.is_dir() else ''} [{kind}]")
                if entry.is_dir():
                    walk(entry, current_depth + 1)

        walk(base, 1)
        window = entries[start - 1 : start - 1 + limit]
        return ToolResult(
            output="\n".join(window),
            success=True,
            metadata={"count": len(entries), "returned": len(window), "more": len(entries) > start - 1 + limit},
        )


class ViewImageTool(Tool):
    name = "view_image"
    description = "Attach a local image path for context."

    def run(self, path: str) -> ToolResult:
        p = Path(path)
        if not p.exists():
            return ToolResult(output="image not found", success=False, metadata=None)
        return ToolResult(output=f"attached {p}", success=True, metadata={"path": str(p)})


class TestSyncTool(Tool):
    name = "test_sync_tool"
    description = "Internal test helper with optional sleeps/barrier."
    _barriers: dict[str, threading.Barrier] = {}
    _lock = threading.Lock()

    def run(
        self,
        sleep_before_ms: int | None = None,
        sleep_after_ms: int | None = None,
        barrier: dict[str, Any] | None = None,
    ) -> ToolResult:
        if sleep_before_ms:
            time.sleep(sleep_before_ms / 1000.0)
        if barrier:
            bid = str(barrier.get("id", "default"))
            participants = int(barrier.get("participants", 1))
            timeout_s = barrier.get("timeout_ms")
            timeout = (timeout_s / 1000.0) if timeout_s else None
            with self._lock:
                if bid not in self._barriers:
                    self._barriers[bid] = threading.Barrier(participants)
                bar = self._barriers[bid]
            try:
                bar.wait(timeout=timeout)
            except threading.BrokenBarrierError:
                return ToolResult(output="barrier broken/timeout", success=False, metadata={"id": bid})
            finally:
                if bar.broken or bar.n_waiting == 0:
                    with self._lock:
                        self._barriers.pop(bid, None)
        if sleep_after_ms:
            time.sleep(sleep_after_ms / 1000.0)
        return ToolResult(output="ok", success=True, metadata=None)
