from __future__ import annotations

from typing import Any, Dict

import httpx

from codax.safety import ActionType, SafetyPolicy, guard_action
from codax.tools.base import Tool, ToolResult


class HttpTool(Tool):
    name = "http"
    description = "Perform HTTP requests (GET/POST) with headers and body."

    def __init__(
        self,
        allow_network: bool = True,
        client: httpx.Client | None = None,
        policy: SafetyPolicy | None = None,
    ) -> None:
        self.allow_network = allow_network
        self.client = client or httpx.Client(timeout=20)
        self.policy = policy

    def run(
        self,
        method: str,
        url: str,
        headers: Dict[str, str] | None = None,
        params: Dict[str, str] | None = None,
        json: Dict[str, Any] | None = None,
        data: Any | None = None,
        timeout: int = 20,
    ) -> ToolResult:
        if not self.allow_network:
            return ToolResult(output="network access disabled", success=False, metadata=None)

        action = ActionType.HTTP_POST if method.lower() == "post" else ActionType.UNKNOWN
        if self.policy:
            safety = guard_action(self.policy, action, f"{method.upper()} {url}")
            if safety:
                return safety

        try:
            response = self.client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json,
                data=data,
                timeout=timeout,
            )
            body = response.text
            content_type = response.headers.get("content-type", "")
            if "xml" not in content_type and len(body) > 20000:
                body = body[:20000] + "\n[truncated]"
            elapsed_ms = None
            try:
                if response.elapsed is not None:
                    elapsed_ms = response.elapsed.total_seconds() * 1000
            except RuntimeError:
                elapsed_ms = None
            metadata = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "elapsed_ms": elapsed_ms,
            }
            return ToolResult(output=body, success=response.is_success, metadata=metadata)
        except httpx.HTTPError as exc:
            return ToolResult(output=str(exc), success=False, metadata=None)
