from codax.config import Settings
from codax.safety import build_policy
from codax.tools.filesystem import (
    FsGlobTool,
    FsListTool,
    FsMkdirTool,
    FsReadTool,
    FsRemoveTool,
    FsWriteTool,
)
from codax.tools.git_tools import (
    GitApplyPatchTool,
    GitBranchesTool,
    GitCommitTool,
    GitDiffTool,
    GitShowTool,
    GitStatusTool,
)
from codax.tools.http_tool import HttpTool
from codax.tools.search_tool import SearchTool
from codax.tools.shell import ShellTool
from codax.tools.text_tools import AnalyzeTool, SummarizeTool
from codax.tools.llm_node import LlmNodeTool
from codax.tools.workflow_tools import WorkflowRunTool, WorkflowValidateTool
from codax.tools.advanced import (
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

__all__ = [
    "ShellTool",
    "ShellCommandTool",
    "ExecCommandTool",
    "WriteStdinTool",
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
    "ApplyPatchTool",
    "UpdatePlanTool",
    "GrepFilesTool",
    "ReadFileAdvancedTool",
    "ListDirAdvancedTool",
    "ViewImageTool",
    "TestSyncTool",
    "SummarizeTool",
    "AnalyzeTool",
    "WorkflowValidateTool",
    "WorkflowRunTool",
    "LlmNodeTool",
    "build_tool_registry",
]


def build_tool_registry(settings: Settings) -> dict[str, object]:
    """Instantiate all tools with project settings and safety policy."""
    workspace = settings.workspace_root
    allow_network = settings.allow_network
    policy = build_policy(settings)
    registry: dict[str, object] = {
        "shell": ShellTool(policy=policy, timeout=settings.request_timeout_seconds),
        "shell_command": ShellCommandTool(workspace, timeout=settings.request_timeout_seconds),
        "exec_command": ExecCommandTool(workspace, timeout_ms=settings.request_timeout_seconds * 1000),
        "write_stdin": WriteStdinTool(),
        "fs_read": FsReadTool(workspace),
        "fs_write": FsWriteTool(workspace),
        "fs_list": FsListTool(workspace),
        "fs_mkdir": FsMkdirTool(workspace),
        "fs_remove": FsRemoveTool(workspace, policy),
        "fs_glob": FsGlobTool(workspace),
        "grep_files": GrepFilesTool(workspace),
        "read_file": ReadFileAdvancedTool(),
        "list_dir": ListDirAdvancedTool(),
        "git_status": GitStatusTool(workspace),
        "git_diff": GitDiffTool(workspace),
        "git_show": GitShowTool(workspace),
        "git_apply_patch": GitApplyPatchTool(workspace),
        "git_branches": GitBranchesTool(workspace),
        "git_commit": GitCommitTool(workspace, policy),
        "http": HttpTool(allow_network=allow_network, policy=policy),
        "search": SearchTool(settings),
        "fetch_url": HttpTool(allow_network=allow_network, policy=policy),
        "apply_patch": ApplyPatchTool(workspace),
        "update_plan": UpdatePlanTool(),
        "view_image": ViewImageTool(),
        "test_sync_tool": TestSyncTool(),
        "summarize": SummarizeTool(settings),
        "analyze": AnalyzeTool(),
        "llm_node": LlmNodeTool(settings),
        "workflow_validate": WorkflowValidateTool(workspace),
        "workflow_run": WorkflowRunTool(workspace),
    }
    return registry
