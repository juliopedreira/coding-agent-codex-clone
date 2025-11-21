from __future__ import annotations

from typing import Any, Dict

from codex.config import Settings
from codex.tools import build_tool_registry
from codex.tools.text_tools import AnalyzeTool, SummarizeTool


def create_agent_graph(settings: Settings) -> Any:
    """
    Placeholder for LangGraph assembly.

    Returns
    -------
    Any
        Future: LangGraph graph object configured with tools and LLM client.
    """
    raise NotImplementedError("Agent graph assembly is not implemented yet.")


def run_prompt(prompt: str, settings: Settings) -> Dict[str, Any]:
    """
    Default lightweight workflow when no workflow file is provided.

    Steps:
    1) analyze prompt text (word/char counts).
    2) summarize prompt text to a concise form.
    """
    registry = build_tool_registry(settings)
    analyze_tool: AnalyzeTool = registry["analyze"]  # type: ignore[assignment]
    summarize_tool: SummarizeTool = registry["summarize"]  # type: ignore[assignment]

    analysis = analyze_tool.run(prompt)
    summary = summarize_tool.run(prompt, max_tokens=80)

    return {
        "analysis": analysis.output,
        "summary": summary.output,
        "metadata": {
            "analysis": analysis.metadata,
            "summary": summary.metadata,
        },
    }
