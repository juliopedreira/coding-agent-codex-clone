import json

from codax.config import Settings
from codax.tools.llm_node import LlmNodeTool
from codax.tools.workflow_tools import StepRecord, _render_value, _select_context
from codax.workflows import compiler


def test_load_workflow_parses_json(tmp_path) -> None:
    wf_path = tmp_path / "wf.json"
    wf_path.write_text(json.dumps({"steps": []}), encoding="utf-8")
    data = compiler.load_workflow(wf_path)
    assert data["steps"] == []


def test_compile_workflow_runs(tmp_path) -> None:
    wf_path = tmp_path / "wf.json"
    wf_path.write_text(json.dumps({"steps": []}), encoding="utf-8")
    compiled = compiler.load_and_compile(wf_path)
    result = compiled.run()
    assert "success" in result


def test_render_value_supports_step_context() -> None:
    ctx = {
        "steps": {
            "Failing": StepRecord(output="boom", metadata=None, success=False),
        }
    }
    rendered = _render_value("{{steps['Failing'].output}}", ctx)
    assert rendered == "boom"


def test_llm_node_fallback_json() -> None:
    tool = LlmNodeTool(Settings(openai_api_key=None))
    schema = {"bullets": [""], "status": ""}
    result = tool.run(system_prompt="s", user_message="explain", json_schema=schema)
    assert result.success
    assert isinstance(result.output, dict)
    assert "bullets" in result.output


def test_select_context_keys_are_passed() -> None:
    ctx = {"foo": "bar", "steps": {"X": StepRecord(output="baz", metadata=None, success=True)}}
    selected = _select_context(ctx, ["foo", "X", "missing"])
    assert selected["foo"] == "bar"
    assert selected["X"] == "baz"
    assert "missing" in selected
