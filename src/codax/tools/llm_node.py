from __future__ import annotations

import json
from typing import Any, Dict, List

from codax.config import Settings
from codax.tools.base import Tool, ToolResult

try:  # Optional dependency
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - optional runtime dep
    ChatOpenAI = None  # type: ignore[assignment]


def _fallback_response(user_message: str, json_schema: Dict[str, Any] | None = None) -> str:
    if json_schema:
        # Build a minimal JSON object using schema keys.
        payload = {}
        for key, default in json_schema.items():
            if isinstance(default, list):
                payload[key] = default
            elif isinstance(default, dict):
                payload[key] = default
            else:
                payload[key] = str(default)
        return json.dumps(payload)
    words = user_message.split()
    return " ".join(words[:40]) + ("..." if len(words) > 40 else "")


class LlmNodeTool(Tool):
    name = "llm_node"
    description = "Single-turn LLM node with system/user prompts and optional JSON output."
    accepts_context = True

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    def run(  # type: ignore[override]
        self,
        system_prompt: str,
        user_message: str,
        tools: List[str] | None = None,
        json_schema: Dict[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int = 512,
        context: Dict[str, Any] | None = None,
    ) -> ToolResult:
        temperature = temperature if temperature is not None else self.settings.temperature
        model_used = "heuristic"
        raw_content: str

        prompt_message = user_message
        if json_schema:
            keys = ", ".join(json_schema.keys())
            prompt_message = (
                f"{user_message}\nReturn a JSON object with keys: {keys}. "
                "Keep values concise."
            )

        if context:
            try:
                ctx_json = json.dumps(context, ensure_ascii=False, default=str)
                prompt_message += f"\nContext JSON:\n{ctx_json}"
            except Exception:
                prompt_message += "\n(Context serialization failed; using raw context omitted.)"

        if ChatOpenAI and self.settings.openai_api_key:
            try:
                llm = ChatOpenAI(
                    model=self.settings.model,
                    temperature=temperature,
                    openai_api_key=self.settings.openai_api_key,
                    max_tokens=max_tokens,
                )
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt_message},
                ]
                resp = llm.invoke(messages)
                raw_content = str(getattr(resp, "content", ""))
                model_used = self.settings.model
            except Exception:  # noqa: BLE001
                raw_content = _fallback_response(prompt_message, json_schema)
        else:
            raw_content = _fallback_response(prompt_message, json_schema)

        parsed: Any = None
        if json_schema:
            try:
                parsed = json.loads(raw_content)
            except Exception:
                parsed = None

        output_value = parsed if parsed is not None else raw_content
        metadata = {
            "model": model_used,
            "raw": raw_content,
            "json_schema": bool(json_schema),
            "tools_available": tools or [],
        }
        return ToolResult(output=output_value, success=True, metadata=metadata)
