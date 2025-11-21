from __future__ import annotations

import json
import subprocess
from pathlib import Path

import httpx

from codex.config import Settings
from codex.tools import build_tool_registry
from codex.tools.filesystem import (
    FsGlobTool,
    FsListTool,
    FsMkdirTool,
    FsReadTool,
    FsRemoveTool,
    FsWriteTool,
)
from codex.tools.git_tools import (
    GitApplyPatchTool,
    GitBranchesTool,
    GitCommitTool,
    GitDiffTool,
    GitShowTool,
    GitStatusTool,
)
from codex.tools.http_tool import HttpTool
from codex.tools.search_tool import SearchTool
from codex.tools.shell import ShellTool
from codex.tools.text_tools import AnalyzeTool, SummarizeTool
from codex.tools.workflow_tools import WorkflowRunTool, WorkflowValidateTool


def test_filesystem_tools(tmp_path: Path) -> None:
    reader = FsReadTool(tmp_path)
    writer = FsWriteTool(tmp_path)
    lister = FsListTool(tmp_path)
    mkdir = FsMkdirTool(tmp_path)
    remover = FsRemoveTool(tmp_path)
    globber = FsGlobTool(tmp_path)

    mkdir.run("dir")
    writer.run("dir/hello.txt", "hi")
    assert reader.run("dir/hello.txt").output == "hi"

    listing = lister.run("dir")
    assert "hello.txt" in listing.output

    glob_result = globber.run("dir/*.txt")
    assert "dir/hello.txt" in glob_result.output

    removal = remover.run("dir", recursive=True)
    assert removal.success is True


def test_shell_tool(tmp_path: Path) -> None:
    tool = ShellTool(timeout=2)
    result = tool.run("echo test", cwd=str(tmp_path))
    assert result.success is True
    assert "test" in result.output


def test_git_tools(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Dev"], cwd=tmp_path, check=True)
    (tmp_path / "file.txt").write_text("hello\n")
    subprocess.run(["git", "add", "file.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True)

    status = GitStatusTool(tmp_path).run()
    assert status.success

    diff = GitDiffTool(tmp_path).run()
    assert diff.success

    show = GitShowTool(tmp_path).run()
    assert show.success

    patch = """\
diff --git a/file.txt b/file.txt
index e965047..b6fc4c6 100644
--- a/file.txt
+++ b/file.txt
@@ -1 +1 @@
-hello
+hello world
"""
    apply = GitApplyPatchTool(tmp_path).run(patch=patch)
    assert apply.success
    assert "world" in (tmp_path / "file.txt").read_text()

    branches = GitBranchesTool(tmp_path).run()
    assert branches.success


def test_git_commit_allow_flag(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Dev"], cwd=tmp_path, check=True)
    (tmp_path / "file.txt").write_text("hello\n")
    subprocess.run(["git", "add", "file.txt"], cwd=tmp_path, check=True)
    tool_disabled = GitCommitTool(tmp_path, allow_commits=False)
    result_disabled = tool_disabled.run(message="msg")
    assert result_disabled.success is False

    tool_enabled = GitCommitTool(tmp_path, allow_commits=True)
    result_enabled = tool_enabled.run(message="msg", all=True)
    assert result_enabled.success is True


def test_http_tool_mock() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # type: ignore[override]
        return httpx.Response(200, text="{\"ok\": true}", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    tool = HttpTool(allow_network=True, client=client)
    result = tool.run("GET", "https://example.com")
    assert result.success
    assert "ok" in result.output


def test_search_tool_mock() -> None:
    response_payload = {"Results": [{"Text": "Title", "FirstURL": "http://example.com"}]}

    def handler(request: httpx.Request) -> httpx.Response:  # type: ignore[override]
        return httpx.Response(200, json=response_payload, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    tool = SearchTool(allow_network=True, client=client)
    result = tool.run("query")
    assert result.success
    assert "example.com" in result.output
    assert result.metadata and result.metadata["results"][0]["url"] == "http://example.com"


def test_text_tools() -> None:
    summarize = SummarizeTool()
    text = " ".join(["word"] * 100)
    summary = summarize.run(text, max_tokens=10)
    assert summary.success
    assert summary.metadata and summary.metadata["summary_words"] == 20  # floor limit

    analyze = AnalyzeTool()
    analysis = analyze.run("one two three")
    assert analysis.success
    assert analysis.metadata and analysis.metadata["word_count"] == 3


def test_workflow_tools(tmp_path: Path) -> None:
    wf = {
        "steps": [
            {"id": "write", "tool": "fs_write", "args": {"path": "out.txt", "content": "data"}},
            {"id": "read", "tool": "fs_read", "args": {"path": "out.txt"}, "assign": "text"},
            {
                "id": "echo",
                "tool": "shell",
                "args": {"command": "echo {{text}}", "cwd": str(tmp_path)},
            },
        ]
    }
    wf_path = tmp_path / "workflow.json"
    wf_path.write_text(json.dumps(wf))

    validator = WorkflowValidateTool(tmp_path)
    validation = validator.run(str(wf_path))
    assert validation.success
    assert validation.metadata and validation.metadata["step_count"] == 3

    settings = Settings(workspace_root=tmp_path, allow_network=False, request_timeout_seconds=5)
    registry = build_tool_registry(settings)
    runner = WorkflowRunTool(tmp_path)
    run_result = runner.run(str(wf_path), params={"x": "1"}, registry=registry)
    assert run_result.success
    assert run_result.metadata
    assert "workflow completed" in run_result.output
    assert "echo" in "\n".join(run_result.metadata["transcript"])


def test_workflow_validation_failure(tmp_path: Path) -> None:
    wf_path = tmp_path / "workflow.json"
    wf_path.write_text(json.dumps({"not_steps": []}))
    validator = WorkflowValidateTool(tmp_path)
    result = validator.run(str(wf_path))
    assert result.success is False

    wf_path.write_text(json.dumps({"steps": "not-a-list"}))
    result_not_list = validator.run(str(wf_path))
    assert result_not_list.success is False

    missing = validator.run(str(tmp_path / "absent.json"))
    assert missing.success is False


def test_search_network_disabled() -> None:
    tool = SearchTool(allow_network=False)
    result = tool.run("hello")
    assert result.success is False
    assert "disabled" in result.output


def test_search_error_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # type: ignore[override]
        raise httpx.ConnectError("boom", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    tool = SearchTool(allow_network=True, client=client)
    result = tool.run("query")
    assert result.success is False


def test_build_tool_registry(tmp_path: Path) -> None:
    settings = Settings(workspace_root=tmp_path, allow_network=False, request_timeout_seconds=1)
    registry = build_tool_registry(settings)
    expected_keys = {
        "shell",
        "fs_read",
        "fs_write",
        "fs_list",
        "fs_mkdir",
        "fs_remove",
        "fs_glob",
        "git_status",
        "git_diff",
        "git_show",
        "git_apply_patch",
        "git_branches",
        "git_commit",
        "http",
        "search",
        "summarize",
        "analyze",
        "workflow_validate",
        "workflow_run",
    }
    assert set(registry) == expected_keys
