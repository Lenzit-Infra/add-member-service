import logging
import os
from logging.handlers import RotatingFileHandler
from app.core.logging_config import _resilient_stdout, _HandlerStreamProxy


def test_resilient_stdout_does_not_raise_on_emoji_or_persian_text():
    stream = _resilient_stdout()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger("test_resilient_stdout")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        logger.info("⚠️ تست فارسی و ایموجی")  # must not raise, even on cp1252 consoles
    finally:
        logger.removeHandler(handler)


def test_handler_stream_proxy_survives_rotation(tmp_path, capsys):
    log_path = str(tmp_path / "rotate_test.log")
    handler = RotatingFileHandler(log_path, maxBytes=200, backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger("test_rotation")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    proxy = _HandlerStreamProxy(handler)

    try:
        for i in range(40):
            logger.info(f"log line number {i} padded to force rotation soon enough")
            proxy.write(f"print-tee line {i}\n")  # simulates a concurrent print() call

        assert os.path.exists(log_path + ".1"), "rotation should have happened at least once"
        # The bug this guards against: a second handle held open on the same
        # path blocks Windows rotation, which then loops a PermissionError on
        # every emit() (printed via logging's own error path to stderr, not
        # raised — so it must be checked here, not with pytest.raises).
        captured = capsys.readouterr()
        assert "PermissionError" not in captured.err
        assert "Logging error" not in captured.err
    finally:
        logger.removeHandler(handler)
        handler.close()
