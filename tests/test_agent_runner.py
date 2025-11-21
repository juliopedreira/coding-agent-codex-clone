import pytest

from codex.agent import runner
from codex.config import Settings


def test_create_agent_graph_not_implemented() -> None:
    settings = Settings(_env_file=None)
    with pytest.raises(NotImplementedError):
        runner.create_agent_graph(settings)


def test_run_prompt_returns_summary() -> None:
    settings = Settings(_env_file=None)
    result = runner.run_prompt(
        "hi there prompt", settings, model_override="m1", reasoning="standard"
    )
    assert "summary" in result
    assert "analysis" in result
    assert result["model"] == "m1"
    assert result["reasoning"] == "standard"
