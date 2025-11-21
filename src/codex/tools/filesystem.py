from __future__ import annotations

import glob
import os
import shutil
from pathlib import Path

from codex.tools.base import Tool, ToolResult


def _ensure_workspace(path: Path, workspace_root: Path) -> Path:
    resolved = (
        (workspace_root / path).expanduser().resolve()
        if not path.is_absolute()
        else path.expanduser().resolve()
    )
    if not str(resolved).startswith(str(workspace_root)):
        raise ValueError(f"Path {resolved} escapes workspace {workspace_root}")
    return resolved


def _detect_binary(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            chunk = handle.read(1024)
            return b"\0" in chunk
    except FileNotFoundError:
        return False


class FsReadTool(Tool):
    name = "fs_read"
    description = "Read text file content from the workspace."

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def run(self, path: str, encoding: str = "utf-8") -> ToolResult:
        target = _ensure_workspace(Path(path), self.workspace_root)
        if not target.exists():
            return ToolResult(output="File not found", success=False, metadata=None)
        if _detect_binary(target):
            return ToolResult(output="Binary file blocked", success=False, metadata=None)
        content = target.read_text(encoding=encoding)
        return ToolResult(
            output=content, success=True, metadata={"bytes_read": len(content.encode(encoding))}
        )


class FsWriteTool(Tool):
    name = "fs_write"
    description = "Write or append text to a file in the workspace."

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def run(
        self, path: str, content: str, encoding: str = "utf-8", append: bool = False
    ) -> ToolResult:
        target = _ensure_workspace(Path(path), self.workspace_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        target.open(mode, encoding=encoding).write(content)
        return ToolResult(
            output="ok",
            success=True,
            metadata={"bytes_written": len(content.encode(encoding)), "mode": mode},
        )


class FsListTool(Tool):
    name = "fs_list"
    description = "List directory entries."

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def run(self, path: str) -> ToolResult:
        target = _ensure_workspace(Path(path), self.workspace_root)
        if not target.exists():
            return ToolResult(output="Path not found", success=False, metadata=None)
        entries = sorted(os.listdir(target))
        return ToolResult(
            output="\n".join(entries),
            success=True,
            metadata={"entries": entries, "count": len(entries)},
        )


class FsMkdirTool(Tool):
    name = "fs_mkdir"
    description = "Create a directory."

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def run(self, path: str, parents: bool = True, exist_ok: bool = True) -> ToolResult:
        target = _ensure_workspace(Path(path), self.workspace_root)
        target.mkdir(parents=parents, exist_ok=exist_ok)
        return ToolResult(output="created", success=True, metadata={"created": True})


class FsRemoveTool(Tool):
    name = "fs_remove"
    description = "Remove a file or directory."

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def run(self, path: str, recursive: bool = False, force: bool = False) -> ToolResult:
        target = _ensure_workspace(Path(path), self.workspace_root)
        if not target.exists():
            if force:
                return ToolResult(output="not found", success=True, metadata={"removed": False})
            return ToolResult(output="not found", success=False, metadata={"removed": False})

        if target.is_dir():
            if not recursive:
                return ToolResult(
                    output="directory removal requires recursive=True", success=False, metadata=None
                )
            shutil.rmtree(target)
        else:
            target.unlink()
        return ToolResult(output="removed", success=True, metadata={"removed": True})


class FsGlobTool(Tool):
    name = "fs_glob"
    description = "Glob for files relative to the workspace."

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def run(self, pattern: str) -> ToolResult:
        base_pattern = str(_ensure_workspace(self.workspace_root / pattern, self.workspace_root))
        matches = [Path(match).resolve() for match in glob.glob(base_pattern)]
        rel_matches = [str(match.relative_to(self.workspace_root)) for match in matches]
        return ToolResult(
            output="\n".join(rel_matches), success=True, metadata={"matches": rel_matches}
        )
