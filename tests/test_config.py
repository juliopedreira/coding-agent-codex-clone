from pathlib import Path

from codex.config import Settings, get_settings


def test_settings_workspace_expands(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("WORKSPACE_ROOT", str(tmp_path))
    settings = Settings(_env_file=None)
    assert settings.workspace_root == tmp_path.resolve()
    assert settings.openai_api_key == "test-key"


def test_settings_cached(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    first = get_settings()
    second = get_settings()
    assert first is second
