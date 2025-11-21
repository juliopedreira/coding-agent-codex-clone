from codex.config import Settings
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

__all__ = [
    "ShellTool",
    "FsReadTool",
    "FsWriteTool",
    "FsListTool",
    "FsMkdirTool",
    "FsRemoveTool",
    "FsGlobTool",
    "GitStatusTool",
    "GitDiffTool",
    "GitShowTool",
    "GitApplyPatchTool",
    "GitBranchesTool",
    "GitCommitTool",
    "HttpTool",
    "SearchTool",
    "SummarizeTool",
    "AnalyzeTool",
    "WorkflowValidateTool",
    "WorkflowRunTool",
    "build_tool_registry",
]


def build_tool_registry(settings: Settings) -> dict[str, object]:
    """Instantiate all tools with project settings."""
    workspace = settings.workspace_root
    allow_network = settings.allow_network
    registry: dict[str, object] = {
        "shell": ShellTool(timeout=settings.request_timeout_seconds),
        "fs_read": FsReadTool(workspace),
        "fs_write": FsWriteTool(workspace),
        "fs_list": FsListTool(workspace),
        "fs_mkdir": FsMkdirTool(workspace),
        "fs_remove": FsRemoveTool(workspace),
        "fs_glob": FsGlobTool(workspace),
        "git_status": GitStatusTool(workspace),
        "git_diff": GitDiffTool(workspace),
        "git_show": GitShowTool(workspace),
        "git_apply_patch": GitApplyPatchTool(workspace),
        "git_branches": GitBranchesTool(workspace),
        "git_commit": GitCommitTool(workspace, allow_commits=False),
        "http": HttpTool(allow_network=allow_network),
        "search": SearchTool(allow_network=allow_network),
        "summarize": SummarizeTool(),
        "analyze": AnalyzeTool(),
        "workflow_validate": WorkflowValidateTool(workspace),
        "workflow_run": WorkflowRunTool(workspace),
    }
    return registry
