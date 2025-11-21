from __future__ import annotations

from codex.tools.base import Tool, ToolResult


class SummarizeTool(Tool):
    name = "summarize"
    description = "Summarize provided text using a lightweight heuristic."

    def run(self, text: str, max_tokens: int = 512, style: str | None = None) -> ToolResult:
        words = text.split()
        limit = max(20, max_tokens)
        summary_words = words[:limit]
        suffix = "..." if len(words) > limit else ""
        summary = " ".join(summary_words) + suffix
        metadata = {
            "original_words": len(words),
            "summary_words": len(summary_words),
            "style": style,
        }
        return ToolResult(output=summary, success=True, metadata=metadata)


class AnalyzeTool(Tool):
    name = "analyze"
    description = "Return simple text statistics."

    def run(self, text: str) -> ToolResult:
        words = text.split()
        characters = len(text)
        word_count = len(words)
        reading_time_minutes = round(word_count / 200, 2) if word_count else 0.0
        metadata = {
            "word_count": word_count,
            "character_count": characters,
            "reading_time_minutes": reading_time_minutes,
        }
        summary = (
            f"words={word_count}, characters={characters}, "
            f"reading_time_minutes={reading_time_minutes}"
        )
        return ToolResult(output=summary, success=True, metadata=metadata)
