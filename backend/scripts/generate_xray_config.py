# generate_xray_config.py
# Reads TELEGRAM_PROXIES from .env and writes backend/xray-config.json — the
# config xray-core needs to fan out to every listed vless/vmess/ss server and
# auto-route through whichever has the best live ping (leastPing balancer).
#
# Re-run this any time you add/remove/reorder proxy links in .env, then
# restart xray-core for the change to take effect.
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core import config
from app.core.proxy_links import build_xray_config, resolve_proxy_links

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "xray-config.json")


def main():
    links = resolve_proxy_links()
    if not links:
        print("No proxy links available (no TELEGRAM_PROXY_SUBSCRIPTION_URL or TELEGRAM_PROXIES configured in .env) — nothing to generate.")
        return

    xray_config = build_xray_config(links, config.TELEGRAM_PROXY_SOCKS_PORT)
    parsed_count = len(xray_config["outbounds"]) - 1  # minus the "direct" fallback
    total_count = len(links)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(xray_config, f, indent=2)

    print(f"Wrote {OUTPUT_PATH} — {parsed_count}/{total_count} proxy links parsed successfully.")
    if parsed_count < total_count:
        print("Some links failed to parse and were skipped (unsupported scheme or malformed URL).")


if __name__ == "__main__":
    main()
