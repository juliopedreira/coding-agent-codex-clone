import logging
from pathlib import Path

from codax.config import Settings
from codax.logging import RunContext, setup_json_logging


def test_setup_json_logging_emits_json(capsys, tmp_path: Path) -> None:
    settings = Settings(logs_dir=tmp_path, data_dir=tmp_path, config_file=tmp_path / "c.toml")
    run_ctx = RunContext(run_id="test")
    setup_json_logging(level=logging.INFO, settings=settings, run=run_ctx)
    logging.getLogger("codax.test").info("hello")
    captured = capsys.readouterr().out.strip()
    assert '"message": "hello"' in captured
    assert tmp_path.joinpath("codax.log").exists()
