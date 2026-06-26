# proxy_supervisor.py
# Owns the xray-core process: resolves the current proxy list (subscription
# URL first, static TELEGRAM_PROXIES fallback), regenerates xray-config.json,
# and (re)launches xray-core — only restarting it when the list actually
# changed, or if it died on its own. Runs forever; intended to be started
# once by start_production.ps1 alongside the API/worker.
import sys
import os
import json
import time
import subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.logging_config import setup_logging
setup_logging("xray_supervisor")

import logging
from app.core import config
from app.core.proxy_links import build_xray_config, resolve_proxy_links

logger = logging.getLogger("xray_supervisor")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BACKEND_DIR, "xray-config.json")
LOG_PATH = os.path.join(BACKEND_DIR, "logs", "xray.log")


def write_config(links: list) -> int:
    xray_config = build_xray_config(links, config.TELEGRAM_PROXY_SOCKS_PORT)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(xray_config, f, indent=2)
    return len(xray_config["outbounds"]) - 1  # minus the "direct" fallback


def start_xray():
    log_file = open(LOG_PATH, "a", encoding="utf-8")
    return subprocess.Popen(
        [config.XRAY_BINARY_PATH, "run", "-config", CONFIG_PATH],
        cwd=BACKEND_DIR, stdout=log_file, stderr=subprocess.STDOUT,
    )


def stop_xray(proc):
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


CRASH_CHECK_SECONDS = 30  # how often to check xray hasn't died, independent of the (much longer) subscription refresh


def main():
    if not os.path.exists(config.XRAY_BINARY_PATH):
        logger.error(f"xray.exe not found at {config.XRAY_BINARY_PATH} — Telethon will try direct connections instead.")
        return

    refresh_seconds = config.TELEGRAM_PROXY_REFRESH_MINUTES * 60
    last_links = None
    last_refresh_at = 0
    xray_proc = None
    logger.info(f"Proxy supervisor started — refreshing every {config.TELEGRAM_PROXY_REFRESH_MINUTES} minutes.")

    while True:
        now = time.monotonic()
        if now - last_refresh_at >= refresh_seconds:
            links = resolve_proxy_links()
            last_refresh_at = now
            if links and links != last_links:
                count = write_config(links)
                logger.info(f"Proxy list changed — {count} server(s) configured. Restarting xray-core.")
                stop_xray(xray_proc)
                xray_proc = start_xray()
                last_links = links
            elif not links:
                logger.warning("No proxy links available (subscription empty/unreachable and no static fallback configured).")

        if xray_proc and xray_proc.poll() is not None:
            logger.warning("xray-core process exited unexpectedly — restarting with the same config.")
            xray_proc = start_xray()

        time.sleep(CRASH_CHECK_SECONDS)


if __name__ == "__main__":
    main()
