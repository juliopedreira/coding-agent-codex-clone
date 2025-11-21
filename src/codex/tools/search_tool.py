from __future__ import annotations

from typing import Any, Dict, List

import httpx

from codex.tools.base import Tool, ToolResult


class SearchTool(Tool):
    name = "search"
    description = "Web search returning snippets and links."

    def __init__(self, allow_network: bool = True, client: httpx.Client | None = None) -> None:
        self.allow_network = allow_network
        self.client = client or httpx.Client(timeout=10)

    def run(self, query: str, num_results: int = 5) -> ToolResult:
        if not self.allow_network:
            return ToolResult(output="network access disabled", success=False, metadata=None)

        url = "https://api.duckduckgo.com/"
        try:
            response = self.client.get(
                url,
                params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
            )
            data = response.json()
        except Exception as exc:  # broad to avoid extra deps
            return ToolResult(output=str(exc), success=False, metadata=None)

        results: List[Dict[str, Any]] = []
        # DuckDuckGo JSON has both Results and RelatedTopics sections.
        if isinstance(data, dict):
            for item in data.get("Results", []):
                if len(results) >= num_results:
                    break
                results.append(
                    {
                        "title": item.get("Text", ""),
                        "url": item.get("FirstURL", ""),
                        "snippet": item.get("Text", ""),
                    }
                )
            for topic in data.get("RelatedTopics", []):
                if len(results) >= num_results:
                    break
                if isinstance(topic, dict) and "FirstURL" in topic:
                    results.append(
                        {
                            "title": topic.get("Text", ""),
                            "url": topic.get("FirstURL", ""),
                            "snippet": topic.get("Text", ""),
                        }
                    )

        output_lines = [f"{item['title']} — {item['url']}" for item in results]
        return ToolResult(
            output="\n".join(output_lines), success=True, metadata={"results": results}
        )
