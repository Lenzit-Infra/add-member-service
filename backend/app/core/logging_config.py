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


class _SafeConsoleStream:
    """Windows' default console/pipe encoding (cp1252) can't encode emoji or
    non-Latin text (Persian, etc.) — without this, a single such write crashes
    that log call. Wraps (doesn't replace/own) the real stream, so it never
    risks closing the underlying console/pipe — just falls back to
    backslash-escaping on a UnicodeEncodeError instead of raising."""

    def __init__(self, stream):
        self._stream = stream

    def write(self, data):
        try:
            self._stream.write(data)
        except UnicodeEncodeError:
            encoding = getattr(self._stream, "encoding", None) or "ascii"
            self._stream.write(data.encode(encoding, errors="backslashreplace").decode(encoding))

    def flush(self):
        self._stream.flush()

    def isatty(self):
        return getattr(self._stream, "isatty", lambda: False)()


def _resilient_stdout():
    return _SafeConsoleStream(sys.__stdout__)


class _HandlerStreamProxy:
    """Forwards print()-tee writes to a RotatingFileHandler's *current*
    stream (read fresh on every write, never cached) instead of opening a
    second independent handle on the same log path. A second handle held
    open on Windows blocks the handler's own rotation rename — it was
    failing with PermissionError on every log call once a file hit
    maxBytes, in a loop, since the failed rollover never properly clears."""

    def __init__(self, handler):
        self._handler = handler

    def write(self, data):
        stream = self._handler.stream
        if stream:
            try:
                stream.write(data)
                stream.flush()
            except Exception:
                pass

    def flush(self):
        stream = self._handler.stream
        if stream:
            try:
                stream.flush()
            except Exception:
                pass

    def isatty(self):
        return False


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

    console_handler = logging.StreamHandler(_resilient_stdout())
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Catch every existing print() statement too, not just logging.* calls —
    # routed through file_handler's own stream rather than a second handle on
    # the same path, so log rotation (above) keeps working on Windows.
    raw_file = _HandlerStreamProxy(file_handler)
    sys.stdout = _Tee(_resilient_stdout(), raw_file)
    sys.stderr = _Tee(_resilient_stdout(), raw_file)

    return logging.getLogger(name)
