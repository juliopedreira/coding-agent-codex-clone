import logging

from codex.logging import setup_json_logging


def test_setup_json_logging_emits_json(capsys) -> None:
    setup_json_logging(level=logging.INFO)
    logging.getLogger("codex.test").info("hello")
    captured = capsys.readouterr().out.strip()
    assert '"message": "hello"' in captured
