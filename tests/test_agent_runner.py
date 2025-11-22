from codax.agent import runner
from codax.config import Settings


def test_create_agent_graph_returns_graph() -> None:
    settings = Settings(_env_file=None)
    graph = runner.create_agent_graph(settings)
    assert graph.settings == settings
    result = graph.run("hi")
    assert "summary" in result
    # streaming path
    stream = list(graph.stream("hello"))
    assert stream[-1]["type"] == "done"


def test_run_prompt_returns_summary() -> None:
    settings = Settings(_env_file=None)
    result = runner.run_prompt(
        "hi there prompt", settings, model_override="m1", reasoning="standard"
    )
    assert "summary" in result
    assert "analysis" in result
    assert result["model"] == "m1"
    assert result["reasoning"] == "standard"
