# app/core/logging_config.py
"""
Every process (API, worker) writes a persistent, rotating log file under
backend/logs/ in addition to the console, so a bug can be traced after the
fact instead of only being visible in a terminal that's since scrolled away
or closed. Also tees raw stdout/stderr (the many pre-existing print()
statements across the worker/adder/scraper modules) into the same file, so
nothing is lost without having to rewrite every print() call into logging.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")

_configured = set()


class _Tee:
    """Duplicates writes to multiple streams (e.g. real console + log file)."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
                s.flush()
            except Exception:
                pass

    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except Exception:
                pass

    def isatty(self):
        return False


def setup_logging(name: str) -> logging.Logger:
    """Call once, as early as possible, in each process's entrypoint
    (app/main.py for the API, scripts/run_worker.py for the worker).
    `name` becomes the log filename, e.g. setup_logging("worker") -> backend/logs/worker.log"""
    if name in _configured:
        return logging.getLogger(name)
    _configured.add(name)

    os.makedirs(LOGS_DIR, exist_ok=True)
    log_path = os.path.join(LOGS_DIR, f"{name}.log")

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    file_handler = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.__stdout__)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Catch every existing print() statement too, not just logging.* calls.
    raw_file = open(log_path, "a", encoding="utf-8", buffering=1)
    sys.stdout = _Tee(sys.__stdout__, raw_file)
    sys.stderr = _Tee(sys.__stderr__, raw_file)

    return logging.getLogger(name)
