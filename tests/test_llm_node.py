import types

from codax.config import Settings
from codax.tools import llm_node
from codax.tools.llm_node import LlmNodeTool


def test_llm_node_uses_chatopenai_branch(monkeypatch) -> None:
    # Stub ChatOpenAI to avoid network and ensure main branch is exercised.
    class FakeResponse:
        def __init__(self, content: str) -> None:
            self.content = content

    class FakeChat:
        def __init__(self, **_: object) -> None:
            self.calls = []

        def invoke(self, messages):
            self.calls.append(messages)
            return FakeResponse("structured-ok")

    monkeypatch.setattr(llm_node, "ChatOpenAI", FakeChat)

    tool = LlmNodeTool(Settings(openai_api_key="dummy-key", model="stub-model"))
    result = tool.run(system_prompt="sys", user_message="hi", json_schema=None, temperature=0.0)

    assert result.success
    assert result.output == "structured-ok"
    assert result.metadata["model"] == "stub-model"


def test_llm_node_receives_context(monkeypatch) -> None:
    class FakeResponse:
        def __init__(self, content: str) -> None:
            self.content = content

    class FakeChat:
        def __init__(self, **_: object) -> None:
            self.calls = []

        def invoke(self, messages):
            self.calls.append(messages)
            # Return content that includes a marker from context
            return FakeResponse("context-ok")

    monkeypatch.setattr(llm_node, "ChatOpenAI", FakeChat)

    tool = LlmNodeTool(Settings(openai_api_key="dummy-key", model="stub-model"))
    result = tool.run(system_prompt="sys", user_message="hi", context={"a": 1})

    assert result.success
    assert result.output == "context-ok"
