import pytest

from codex.agent import runner
from codex.config import Settings


def test_create_agent_graph_not_implemented() -> None:
    settings = Settings(_env_file=None)
    with pytest.raises(NotImplementedError):
        runner.create_agent_graph(settings)


def test_run_prompt_not_implemented() -> None:
    settings = Settings(_env_file=None)
    with pytest.raises(NotImplementedError):
        runner.run_prompt("hi", settings)
