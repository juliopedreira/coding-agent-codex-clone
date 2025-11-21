from __future__ import annotations

from typing import Any, Dict

from codex.config import Settings


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
    """Stub for running a prompt through the agent graph."""
    _ = prompt
    _ = settings
    raise NotImplementedError("Agent execution is not implemented yet.")
