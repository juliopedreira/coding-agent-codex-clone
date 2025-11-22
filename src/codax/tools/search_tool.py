from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import re
from typing import Any, Dict, List, Protocol

import httpx

from codax.config import Settings
from codax.tools.base import Tool, ToolResult


class SearchBackend(Protocol):
    name: str

    def search(self, query: str, num_results: int = 5) -> list[dict[str, str]]:
        ...


@dataclass
class DuckDuckGoBackend:
    client: httpx.Client
    name: str = "ddg"

    def search(self, query: str, num_results: int = 5) -> list[dict[str, str]]:
        response = self.client.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
        )
        data = response.json()
        results: list[dict[str, str]] = []
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
        return results


@dataclass
class OpenAIWebSearchBackend:
    """
    Lightweight shim mimicking OpenAI `web_search` responses.
    Uses DuckDuckGo as a fallback to avoid requiring live OpenAI creds.
    """

    client: httpx.Client
    name: str = "openai"

    def search(self, query: str, num_results: int = 5) -> list[dict[str, str]]:
        # Fallback to DDG for demo; in production this would invoke the OpenAI web_search tool.
        ddg = DuckDuckGoBackend(self.client)
        return ddg.search(query, num_results=num_results)


def _build_backend(settings: Settings, client: httpx.Client | None = None) -> SearchBackend:
    client = client or httpx.Client(timeout=10)
    if settings.search_backend == "openai":
        return OpenAIWebSearchBackend(client)
    return DuckDuckGoBackend(client)


class SearchTool(Tool):
    name = "search"
    description = "Web search returning snippets and links."

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self.settings = settings
        self.client = client or httpx.Client(timeout=10)
        self.backend = _build_backend(settings, self.client)

    def _fallback_html(self, query: str, num_results: int) -> list[dict[str, str]]:
        """Fallback: scrape DuckDuckGo lite HTML results."""
        url = "https://duckduckgo.com/html/"
        resp = self.client.get(url, params={"q": query, "ia": "news"}, follow_redirects=True)
        html = resp.text
        results: list[dict[str, str]] = []
        # naive extraction of result links and titles
        for match in re.finditer(r'result__a" href="([^"]+)".*?>(.*?)</a>', html):
            href = unescape(match.group(1))
            title = unescape(re.sub("<.*?>", "", match.group(2)))
            results.append({"title": title, "url": href, "snippet": title})
            if len(results) >= num_results:
                break
        return results

    def _fallback_rss(self, query: str, num_results: int) -> list[dict[str, str]]:
        url = "https://news.google.com/rss/search"
        resp = self.client.get(
            url,
            params={"q": query, "hl": "es", "gl": "ES", "ceid": "ES:es"},
            headers={"User-Agent": "Mozilla/5.0"},
        )
        text = resp.text
        results: list[dict[str, str]] = []
        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(text)
            for item in root.findall(".//item")[:num_results]:
                title = item.findtext("title") or ""
                link = item.findtext("link") or ""
                results.append({"title": title, "url": link, "snippet": title})
        except Exception:
            return results
        return results

    def run(self, query: str, num_results: int = 5) -> ToolResult:
        if not self.settings.allow_network:
            return ToolResult(output="network access disabled", success=False, metadata=None)

        try:
            results: List[Dict[str, Any]] = self.backend.search(query, num_results=num_results)
            if not results:
                results = self._fallback_html(query, num_results)
            if not results:
                results = self._fallback_rss(query, num_results)
        except Exception as exc:  # noqa: BLE001
            return ToolResult(output=str(exc), success=False, metadata=None)

        output_lines = [f"{item['title']} — {item['url']}" for item in results if item.get("url")]
        if not output_lines:
            output_lines = ["No results found."]
        return ToolResult(
            output="\n".join(output_lines),
            success=bool(results),
            metadata={"results": results, "backend": self.backend.name},
        )
