# app/core/proxy_links.py
# Parses vless:// / vmess:// / ss:// subscription links (as exported by any
# standard V2Ray/Xray client) into Xray-core outbound JSON objects, so the
# whole list from .env can be handed to a single generated xray-config.json
# with a leastPing balancer — Xray itself probes each one and routes traffic
# through whichever currently has the best (working) ping, with no manual
# switching needed.
import base64
import json
import logging
from urllib.parse import urlparse, parse_qs, unquote
from app.core import config
from app.core.proxy_subscription import fetch_subscription_links

logger = logging.getLogger("proxy_links")


def _b64decode(data: str) -> str:
    data = data.strip()
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode()).decode("utf-8", errors="ignore")


def _stream_settings(network: str, security: str, query: dict, sni_fallback: str = "") -> dict:
    network = network or "tcp"
    stream = {"network": network, "security": security or "none"}

    if security == "tls":
        sni = query.get("sni", [sni_fallback])[0] or sni_fallback
        tls_settings = {"serverName": sni, "allowInsecure": False}
        fp = query.get("fp", [None])[0]
        if fp:
            tls_settings["fingerprint"] = fp
        alpn = query.get("alpn", [None])[0]
        if alpn:
            tls_settings["alpn"] = unquote(alpn).split(",")
        stream["tlsSettings"] = tls_settings

    host_header = query.get("host", [""])[0]
    path = unquote(query.get("path", ["/"])[0] or "/")

    if network == "ws":
        ws = {"path": path}
        if host_header:
            ws["headers"] = {"Host": host_header}
        stream["wsSettings"] = ws
    elif network in ("xhttp", "splithttp"):
        stream["network"] = "xhttp"
        xhttp = {"path": path, "mode": query.get("mode", ["auto"])[0]}
        if host_header:
            xhttp["host"] = host_header
        extra = query.get("extra", [None])[0]
        if extra:
            try:
                xhttp["extra"] = json.loads(unquote(extra))
            except (json.JSONDecodeError, ValueError):
                pass
        stream["xhttpSettings"] = xhttp

    return stream


def _parse_vless(link: str, tag: str) -> dict:
    parsed = urlparse(link)
    query = parse_qs(parsed.query)
    uid = parsed.username
    address, port = parsed.hostname, parsed.port

    return {
        "tag": tag,
        "protocol": "vless",
        "settings": {
            "vnext": [{
                "address": address,
                "port": port,
                "users": [{"id": uid, "encryption": query.get("encryption", ["none"])[0], "flow": query.get("flow", [""])[0]}],
            }]
        },
        "streamSettings": _stream_settings(
            query.get("type", ["tcp"])[0], query.get("security", ["none"])[0], query, sni_fallback=address,
        ),
    }


def _parse_vmess(link: str, tag: str) -> dict:
    raw = link[len("vmess://"):]
    payload = json.loads(_b64decode(raw))
    address, port = payload.get("add"), int(payload.get("port"))
    security = "tls" if payload.get("tls") else "none"
    query = {
        "host": [payload.get("host", "")],
        "path": [payload.get("path", "/")],
        "sni": [payload.get("sni", address)],
    }

    return {
        "tag": tag,
        "protocol": "vmess",
        "settings": {
            "vnext": [{
                "address": address,
                "port": port,
                "users": [{
                    "id": payload.get("id"),
                    "alterId": int(payload.get("aid", 0) or 0),
                    "security": payload.get("scy", "auto"),
                }],
            }]
        },
        "streamSettings": _stream_settings(payload.get("net", "tcp"), security, query, sni_fallback=address),
    }


def _parse_shadowsocks(link: str, tag: str) -> dict:
    parsed = urlparse(link)
    address, port = parsed.hostname, parsed.port
    userinfo = parsed.username or ""
    try:
        method, password = _b64decode(userinfo).split(":", 1)
    except ValueError:
        # Legacy ss:// where the entire "method:password@host:port" is base64'd together.
        decoded = _b64decode(userinfo)
        creds, _, hostport = decoded.partition("@")
        method, password = creds.split(":", 1)
        if hostport:
            address, _, port_str = hostport.partition(":")
            port = int(port_str) if port_str else port

    return {
        "tag": tag,
        "protocol": "shadowsocks",
        "settings": {"servers": [{"address": address, "port": port, "method": method, "password": password}]},
    }


def resolve_proxy_links() -> list:
    """Subscription URL takes priority (it self-updates on the provider's
    side); the static TELEGRAM_PROXIES list in .env is the fallback, used
    if no subscription is configured or the fetch fails."""
    if config.TELEGRAM_PROXY_SUBSCRIPTION_URL:
        try:
            links = fetch_subscription_links(config.TELEGRAM_PROXY_SUBSCRIPTION_URL)
            if links:
                return links
            logger.warning("Proxy subscription returned no links — falling back to static TELEGRAM_PROXIES")
        except Exception:
            logger.exception("Failed to fetch proxy subscription — falling back to static TELEGRAM_PROXIES")
    return config.TELEGRAM_PROXIES


def parse_proxy_link(link: str, tag: str) -> dict:
    link = link.strip()
    if link.startswith("vless://"):
        return _parse_vless(link, tag)
    if link.startswith("vmess://"):
        return _parse_vmess(link, tag)
    if link.startswith("ss://"):
        return _parse_shadowsocks(link, tag)
    raise ValueError(f"Unsupported proxy link scheme: {link[:10]}...")


def build_xray_config(links: list, socks_port: int) -> dict:
    outbounds = []
    balancer_tags = []
    for i, link in enumerate(links):
        tag = f"proxy-{i}"
        try:
            outbounds.append(parse_proxy_link(link, tag))
            balancer_tags.append(tag)
        except Exception:
            continue  # skip a malformed link rather than fail the whole config

    outbounds.append({"tag": "direct", "protocol": "freedom"})

    return {
        "log": {"loglevel": "warning"},
        "inbounds": [{
            "tag": "socks-in",
            "listen": "127.0.0.1",
            "port": socks_port,
            "protocol": "socks",
            "settings": {"auth": "noauth", "udp": False},
        }],
        "outbounds": outbounds,
        "routing": {
            "domainStrategy": "AsIs",
            "balancers": [{"tag": "telegram-balancer", "selector": ["proxy-"], "strategy": {"type": "leastPing"}}],
            "rules": [{"type": "field", "network": "tcp,udp", "balancerTag": "telegram-balancer"}],
        },
        "observatory": {
            "subjectSelector": ["proxy-"],
            "probeUrl": "https://www.gstatic.com/generate_204",
            "probeInterval": "30s",
            "enableConcurrency": True,
        },
    }
