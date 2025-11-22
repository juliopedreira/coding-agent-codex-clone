from __future__ import annotations

import subprocess
from pathlib import Path

from codax.config import Settings
from codax.tools import (
    ApplyPatchTool,
    ExecCommandTool,
    GrepFilesTool,
    ListDirAdvancedTool,
    ReadFileAdvancedTool,
    ShellCommandTool,
    TestSyncTool,
    UpdatePlanTool,
    ViewImageTool,
    WriteStdinTool,
)


def test_shell_command_runs(tmp_path: Path) -> None:
    tool = ShellCommandTool(tmp_path)
    result = tool.run("echo hi", workdir=str(tmp_path))
    assert result.success
    assert "hi" in result.output


def test_exec_command_and_write_stdin(tmp_path: Path) -> None:
    exec_tool = ExecCommandTool(tmp_path)
    result = exec_tool.run("echo ping", workdir=str(tmp_path))
    assert result.success
    assert "ping" in result.output
    session_id = ExecCommandTool.create_session("init")
    writer = WriteStdinTool()
    wres = writer.run(session_id, chars="more")
    assert wres.success
    assert "more" in wres.output


def test_apply_patch(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    (tmp_path / "file.txt").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "file.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True)
    patch = """\
diff --git a/file.txt b/file.txt
index e965047..b6fc4c6 100644
--- a/file.txt
+++ b/file.txt
@@ -1 +1 @@
-hello
+hello world
"""
    tool = ApplyPatchTool(tmp_path)
    res = tool.run(patch)
    assert res.success
    assert "world" in (tmp_path / "file.txt").read_text()


def test_update_plan() -> None:
    tool = UpdatePlanTool()
    plan = [{"step": "one", "status": "pending"}]
    res = tool.run(plan, explanation="test")
    assert res.success
    assert res.metadata and res.metadata["count"] == 1


def test_grep_files(tmp_path: Path) -> None:
    f1 = tmp_path / "a.txt"
    f1.write_text("hello world\n", encoding="utf-8")
    f2 = tmp_path / "b.txt"
    f2.write_text("nothing\n", encoding="utf-8")
    tool = GrepFilesTool(tmp_path)
    res = tool.run("hello", path=str(tmp_path))
    assert res.success
    assert "a.txt" in res.output


def test_read_file_advanced(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("line1\nline2\nline3\n", encoding="utf-8")
    tool = ReadFileAdvancedTool()
    res = tool.run(str(f), offset=2, limit=1)
    assert res.success
    assert "2:" in res.output
    assert "line2" in res.output


def test_list_dir_advanced(tmp_path: Path) -> None:
    (tmp_path / "dir").mkdir()
    (tmp_path / "dir" / "f.txt").write_text("x", encoding="utf-8")
    tool = ListDirAdvancedTool()
    res = tool.run(str(tmp_path), depth=2)
    assert res.success
    assert "f.txt" in res.output


def test_view_image(tmp_path: Path) -> None:
    img = tmp_path / "img.png"
    img.write_bytes(b"\x89PNG")
    tool = ViewImageTool()
    res = tool.run(str(img))
    assert res.success
    assert "attached" in res.output


def test_test_sync_tool_barrier() -> None:
    tool = TestSyncTool()
    barrier = {"id": "b1", "participants": 1}
    res = tool.run(barrier=barrier)
    assert res.success
