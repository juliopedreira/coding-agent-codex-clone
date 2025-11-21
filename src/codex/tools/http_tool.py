from __future__ import annotations

from typing import Any, Dict

import httpx

from codex.tools.base import Tool, ToolResult


class HttpTool(Tool):
    name = "http"
    description = "Perform HTTP requests (GET/POST) with headers and body."

    def __init__(self, allow_network: bool = True, client: httpx.Client | None = None) -> None:
        self.allow_network = allow_network
        self.client = client or httpx.Client(timeout=20)

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
            elapsed_ms = None
            try:
                if response.elapsed is not None:
                    elapsed_ms = response.elapsed.total_seconds() * 1000
                else:
                    elapsed_ms = None
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
