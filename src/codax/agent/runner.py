from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatResult
from langchain_core.runnables import Runnable
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from codax.config import Settings
from codax.tools import build_tool_registry
from codax.tools.search_tool import SearchTool
from codax.tools.text_tools import AnalyzeTool, SummarizeTool

try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - optional dep
    ChatOpenAI = None  # type: ignore[assignment]


class HeuristicChatModel:
    """Fallback chat model that returns a quick summary without network calls."""

    def __init__(self, model: str = "heuristic") -> None:
        self.model = model
        self.tools: list[Any] = []

    def invoke(self, messages: List[HumanMessage] | Dict[str, Any]) -> AIMessage:
        if isinstance(messages, dict):
            # create_react_agent passes {"messages":[...]}
            messages = messages.get("messages", [])
        content = ""
        for msg in messages:
            if isinstance(msg, HumanMessage):
                content += msg.content + " "
        words = content.split()
        summary = " ".join(words[:40]) + ("..." if len(words) > 40 else "")
        return AIMessage(content=summary)

    def batch(self, inputs: list[Any]) -> list[AIMessage]:
        return [self.invoke(item) for item in inputs]

    def stream(self, messages: Any):
        yield self.invoke(messages)

    def bind_tools(self, tools: list[Any]) -> "HeuristicChatModel":
        self.tools = list(tools)
        return self

    def __call__(self, messages: Any) -> AIMessage:
        return self.invoke(messages)


SYSTEM_PROMPT = (
    "You are Codax, a coding assistant with tools. "
    "Use the registered tools when they can help, especially: "
    "- search_tool for any real-world, news, or factual lookup. "
    "- fetch_url to retrieve page content. "
    "- read_file/list_dir for workspace inspection. "
    "Prefer concise answers; always cite tool-derived info in plain text."
)


def _lc_tools_from_registry(registry: dict[str, Any]) -> list[Any]:
    analyze: AnalyzeTool = registry["analyze"]  # type: ignore[assignment]
    summarize: SummarizeTool = registry["summarize"]  # type: ignore[assignment]
    search: SearchTool = registry["search"]  # type: ignore[assignment]
    fs_read = registry.get("fs_read")
    fs_list = registry.get("fs_list")
    http_tool = registry.get("http")

    @tool
    def analyze_tool(text: str) -> str:
        """Return simple text statistics."""
        return analyze.run(text).output

    @tool
    def summarize_tool(text: str, max_tokens: int = 80) -> str:
        """Summarize provided text."""
        return summarize.run(text, max_tokens=max_tokens).output

    @tool
    def search_tool(query: str, num_results: int = 3) -> str:
        """Search the web and return results."""
        result = search.run(query, num_results=num_results)
        return result.output

    tool_list: list[Any] = [analyze_tool, summarize_tool, search_tool]

    if fs_read:
        @tool
        def read_file(path: str, encoding: str = "utf-8") -> str:
            """Read a text file from the workspace."""
            return fs_read.run(path, encoding=encoding).output  # type: ignore[union-attr]

        tool_list.append(read_file)

    if fs_list:
        @tool
        def list_dir(path: str = ".") -> str:
            """List entries in a directory."""
            return fs_list.run(path).output  # type: ignore[union-attr]

        tool_list.append(list_dir)

    if http_tool:
        @tool
        def fetch_url(url: str, method: str = "GET") -> str:
            """Fetch a web page with optional method (GET/POST)."""
            result = http_tool.run(method, url)  # type: ignore[union-attr]
            return result.output

        tool_list.append(fetch_url)

    return tool_list


@dataclass
class AgentGraph:
    settings: Settings
    runnable: Runnable

    def stream(self, prompt: str, reasoning: str | None = None) -> Iterable[Dict[str, str]]:
        input_payload = {"messages": [HumanMessage(content=prompt)]}
        for chunk in self.runnable.stream(input_payload):
            if isinstance(chunk, dict) and "messages" in chunk:
                for msg in chunk["messages"]:
                    if isinstance(msg, AIMessage):
                        for ch in msg.content:
                            yield {"type": "token", "text": ch}
        yield {"type": "done"}

    def run(self, prompt: str, reasoning: str | None = None) -> Dict[str, Any]:
        input_payload = {"messages": [HumanMessage(content=prompt)]}
        result: dict[str, Any] | ChatResult = self.runnable.invoke(input_payload)
        # create_react_agent returns dict with messages
        messages = result.get("messages") if isinstance(result, dict) else []
        ai_messages = [m for m in messages if isinstance(m, AIMessage)]
        summary = ai_messages[-1].content if ai_messages else ""
        # also compute analysis via tool directly for metadata
        registry = build_tool_registry(self.settings)
        analysis = registry["analyze"].run(prompt)  # type: ignore[index]
        return {
            "model": self.settings.model,
            "reasoning": reasoning or self.settings.reasoning_effort,
            "analysis": analysis.output,
            "summary": summary,
            "metadata": {"analysis": analysis.metadata},
        }


def _build_llm(settings: Settings):
    if ChatOpenAI and settings.openai_api_key:
        return ChatOpenAI(
            model=settings.model,
            temperature=settings.temperature,
            openai_api_key=settings.openai_api_key,
            streaming=True,
        )
    return HeuristicChatModel(model="heuristic")


def create_agent_graph(settings: Settings) -> AgentGraph:
    """
    Assemble a LangGraph react agent with registered tools.
    """
    registry = build_tool_registry(settings)
    llm = _build_llm(settings)
    tools = _lc_tools_from_registry(registry)
    runnable = create_react_agent(llm, tools, state_modifier=SYSTEM_PROMPT).with_config(
        {"recursion_limit": 6}
    )
    return AgentGraph(settings=settings, runnable=runnable)


def run_prompt(
    prompt: str, settings: Settings, model_override: str | None = None, reasoning: str | None = None
) -> Dict[str, Any]:
    """
    Run a prompt through the agent graph with tool calling and return result.
    """
    if model_override:
        settings.model = model_override
    if reasoning:
        settings.reasoning_effort = reasoning
    graph = create_agent_graph(settings)
    return graph.run(prompt, reasoning=reasoning)
