from __future__ import annotations

from typing import Any

from codax.config import Settings
from codax.tools.base import Tool, ToolResult

try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - optional dependency at runtime
    ChatOpenAI = None  # type: ignore[assignment]


def _run_llm_summary(text: str, settings: Settings, max_tokens: int) -> str | None:
    """Best-effort LLM summary; returns None if unavailable."""
    if not ChatOpenAI or not settings.openai_api_key:
        return None
    try:
        llm = ChatOpenAI(
            model=settings.model,
            temperature=settings.temperature,
            openai_api_key=settings.openai_api_key,
            max_tokens=max_tokens,
        )
        resp = llm.invoke(f"Summarize concisely:\n{text}")
        return str(resp.content) if resp else None
    except Exception:
        return None


class SummarizeTool(Tool):
    name = "summarize"
    description = "Summarize provided text with LLM fallback to heuristic."

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    def run(self, text: str, max_tokens: int = 512, style: str | None = None) -> ToolResult:
        words = text.split()
        limit = max(20, max_tokens)
        summary_words = words[:limit]
        suffix = "..." if len(words) > limit else ""
        heuristic = " ".join(summary_words) + suffix
        model_used = "heuristic"
        llm_summary = _run_llm_summary(text, self.settings, max_tokens)
        output = llm_summary or heuristic
        if llm_summary:
            model_used = self.settings.model
        metadata = {
            "original_words": len(words),
            "summary_words": len(summary_words),
            "style": style,
            "model": model_used,
        }
        return ToolResult(output=output, success=True, metadata=metadata)


class AnalyzeTool(Tool):
    name = "analyze"
    description = "Return simple text statistics."

    def run(self, text: str) -> ToolResult:
        words = text.split()
        characters = len(text)
        word_count = len(words)
        reading_time_minutes = round(word_count / 200, 2) if word_count else 0.0
        metadata: dict[str, Any] = {
            "word_count": word_count,
            "character_count": characters,
            "reading_time_minutes": reading_time_minutes,
        }
        summary = (
            f"words={word_count}, characters={characters}, "
            f"reading_time_minutes={reading_time_minutes}"
        )
        return ToolResult(output=summary, success=True, metadata=metadata)
