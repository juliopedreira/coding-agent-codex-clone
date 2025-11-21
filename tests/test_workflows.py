import pytest

from codex.workflows import compiler


def test_load_workflow_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        compiler.load_workflow("dummy.yaml")


def test_compile_workflow_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        compiler.compile_workflow({})
