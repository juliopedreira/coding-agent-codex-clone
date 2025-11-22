from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from codax.config import SafetyMode, Settings
from codax.tools.base import ToolResult


class ActionType(str, Enum):
    SHELL = "shell"
    FILE_REMOVE = "file_remove"
    GIT_COMMIT = "git_commit"
    HTTP_POST = "http_post"
    UNKNOWN = "unknown"


ApprovalCallback = Callable[[ActionType, str], bool]


@dataclass
class SafetyPolicy:
    mode: str
    allow_git_commits: bool

    def requires_approval(self, action: ActionType) -> bool:
        if self.mode == SafetyMode.OFF:
            return False
        if self.mode == SafetyMode.SAFE:
            # Always prompt for risky actions
            return True
        # on-request: prompt for risky actions only
        return action in {ActionType.SHELL, ActionType.FILE_REMOVE, ActionType.GIT_COMMIT, ActionType.HTTP_POST}

    def is_blocked(self, action: ActionType) -> bool:
        if action == ActionType.GIT_COMMIT and not self.allow_git_commits:
            return True
        return False


def default_approval_callback(action: ActionType, detail: str) -> bool:
    """
    Default approval handler: auto-approves for on-request/off, denies for safe.
    A real runtime should override this to collect user confirmation.
    """
    _ = detail
    return action != ActionType.UNKNOWN


def guard_action(
    policy: SafetyPolicy,
    action: ActionType,
    detail: str,
    approval_callback: ApprovalCallback | None = None,
) -> ToolResult | None:
    """
    Evaluate safety policy; return ToolResult if action is blocked or denied, otherwise None.
    """
    if policy.is_blocked(action):
        return ToolResult(output=f"Action blocked by policy: {action}", success=False, metadata=None)

    if policy.requires_approval(action):
        approve_fn = approval_callback or default_approval_callback
        approved = approve_fn(action, detail)
        if not approved:
            return ToolResult(output=f"Action requires approval: {detail}", success=False, metadata=None)
    return None


def build_policy(settings: Settings) -> SafetyPolicy:
    return SafetyPolicy(mode=settings.safety_mode, allow_git_commits=settings.allow_git_commits)
