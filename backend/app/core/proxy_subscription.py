# app/core/proxy_subscription.py
import base64
import urllib.request


def fetch_subscription_links(url: str, timeout: float = 15.0) -> list:
    """Downloads a V2Ray/Xray-style subscription (a URL that resolves to either
    plain newline-separated vless/vmess/ss links, or the same thing base64'd
    as a single blob — both are standard, common subscription formats) and
    returns the list of links found. Raises on network failure; callers
    decide the fallback (e.g. keep using the last-known-good list)."""
    req = urllib.request.Request(url, headers={"User-Agent": "Lenzit-Dashboard/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()

    text = raw.decode("utf-8", errors="ignore").strip()
    if not text.startswith(("vless://", "vmess://", "ss://", "trojan://")):
        try:
            padded = text + "=" * (-len(text) % 4)
            text = base64.b64decode(padded).decode("utf-8", errors="ignore")
        except Exception:
            pass

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return [line for line in lines if line.startswith(("vless://", "vmess://", "ss://"))]
