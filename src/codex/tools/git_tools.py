from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List

from codex.tools.base import Tool, ToolResult
from codex.tools.filesystem import _ensure_workspace


class _GitTool(Tool):
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def _run_git(self, args: List[str], repo_path: str | None = None) -> ToolResult:
        repo = _ensure_workspace(Path(repo_path or "."), self.workspace_root)
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr
        return ToolResult(
            output=output,
            success=result.returncode == 0,
            metadata={"returncode": result.returncode},
        )


class GitStatusTool(_GitTool):
    name = "git_status"
    description = "Show git status."

    def run(self, repo_path: str = ".") -> ToolResult:
        return self._run_git(["status", "--short"], repo_path=repo_path)


class GitDiffTool(_GitTool):
    name = "git_diff"
    description = "Show git diff."

    def run(
        self, repo_path: str = ".", rev: str | None = None, paths: list[str] | None = None
    ) -> ToolResult:
        args = ["diff"]
        if rev:
            args.append(rev)
        if paths:
            args.extend(paths)
        return self._run_git(args, repo_path=repo_path)


class GitShowTool(_GitTool):
    name = "git_show"
    description = "Show git object."

    def run(self, repo_path: str = ".", ref: str = "HEAD") -> ToolResult:
        return self._run_git(["show", ref], repo_path=repo_path)


class GitApplyPatchTool(_GitTool):
    name = "git_apply_patch"
    description = "Apply unified diff patch."

    def run(self, repo_path: str = ".", patch: str = "", check: bool = True) -> ToolResult:
        repo = _ensure_workspace(Path(repo_path), self.workspace_root)
        check_args = ["git", "-C", str(repo), "apply"]
        if check:
            check_args.append("--check")
        check_result = subprocess.run(
            check_args,
            input=patch,
            text=True,
            capture_output=True,
        )
        if check_result.returncode != 0:
            output = check_result.stdout + check_result.stderr
            return ToolResult(
                output=output, success=False, metadata={"returncode": check_result.returncode}
            )

        apply_result = subprocess.run(
            ["git", "-C", str(repo), "apply"],
            input=patch,
            text=True,
            capture_output=True,
        )
        output = apply_result.stdout + apply_result.stderr
        return ToolResult(
            output=output,
            success=apply_result.returncode == 0,
            metadata={"returncode": apply_result.returncode},
        )


class GitBranchesTool(_GitTool):
    name = "git_branches"
    description = "List branches."

    def run(self, repo_path: str = ".", all: bool = False) -> ToolResult:  # noqa: A003
        args = ["branch"]
        if all:
            args.append("--all")
        return self._run_git(args, repo_path=repo_path)


class GitCommitTool(_GitTool):
    name = "git_commit"
    description = "Create commit when enabled."

    def __init__(self, workspace_root: Path, allow_commits: bool = False) -> None:
        super().__init__(workspace_root)
        self.allow_commits = allow_commits

    def run(self, repo_path: str = ".", message: str = "", all: bool = False) -> ToolResult:
        if not self.allow_commits:
            return ToolResult(
                output="git commit is disabled by configuration", success=False, metadata=None
            )
        args = ["commit", "-m", message]
        if all:
            args.insert(1, "-a")
        return self._run_git(args, repo_path=repo_path)
