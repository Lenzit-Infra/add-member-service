from app.core.proxy_links import parse_proxy_link, build_xray_config

# All addresses/UUIDs/passwords below are synthetic test fixtures (RFC 5737
# TEST-NET-3 addresses, made-up UUIDs) — never real proxy credentials.

VLESS_WS_TLS = (
    "vless://00000000-1111-2222-3333-444444444444@203.0.113.10:8443"
    "?encryption=none&security=tls&type=ws&headerType=none&path=%2F"
    "&host=example.host&sni=example.host&fp=random"
)

VLESS_TCP_NONE = "vless://00000000-1111-2222-3333-444444444444@203.0.113.11:3803?encryption=none&security=none&type=tcp&headerType=none"

VMESS_LINK = (
    "vmess://eyJhZGQiOiAiMjAzLjAuMTEzLjIwIiwgImFpZCI6ICIwIiwgImhvc3QiOiAiZXhhbXBsZS50ZXN0IiwgImlkIjogIjAwMDAwMDAwLTEx"
    "MTEtMjIyMi0zMzMzLTQ0NDQ0NDQ0NDQ0NCIsICJuZXQiOiAid3MiLCAicGF0aCI6ICIvIiwgInBvcnQiOiAyMDUyLCAicHMiOiAidGVzdCIsICJz"
    "Y3kiOiAiYXV0byIsICJ0eXBlIjogIm5vbmUiLCAidiI6ICIyIn0="
)

SS_LINK = "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTp0ZXN0cGFzc3dvcmQxMjM=@203.0.113.30:123"


def test_parse_vless_ws_tls():
    outbound = parse_proxy_link(VLESS_WS_TLS, "proxy-0")
    assert outbound["protocol"] == "vless"
    vnext = outbound["settings"]["vnext"][0]
    assert vnext["address"] == "203.0.113.10"
    assert vnext["port"] == 8443
    assert vnext["users"][0]["id"] == "00000000-1111-2222-3333-444444444444"
    assert outbound["streamSettings"]["network"] == "ws"
    assert outbound["streamSettings"]["security"] == "tls"
    assert outbound["streamSettings"]["tlsSettings"]["serverName"] == "example.host"
    assert outbound["streamSettings"]["wsSettings"]["headers"]["Host"] == "example.host"


def test_parse_vless_tcp_no_tls():
    outbound = parse_proxy_link(VLESS_TCP_NONE, "proxy-1")
    assert outbound["streamSettings"]["network"] == "tcp"
    assert outbound["streamSettings"]["security"] == "none"
    assert "tlsSettings" not in outbound["streamSettings"]


def test_parse_vmess():
    outbound = parse_proxy_link(VMESS_LINK, "proxy-2")
    assert outbound["protocol"] == "vmess"
    vnext = outbound["settings"]["vnext"][0]
    assert vnext["address"] == "203.0.113.20"
    assert vnext["port"] == 2052
    assert vnext["users"][0]["id"] == "00000000-1111-2222-3333-444444444444"
    assert outbound["streamSettings"]["wsSettings"]["headers"]["Host"] == "example.test"


def test_parse_shadowsocks():
    outbound = parse_proxy_link(SS_LINK, "proxy-3")
    assert outbound["protocol"] == "shadowsocks"
    server = outbound["settings"]["servers"][0]
    assert server["address"] == "203.0.113.30"
    assert server["port"] == 123
    assert server["method"] == "chacha20-ietf-poly1305"
    assert server["password"] == "testpassword123"


def test_build_xray_config_skips_bad_links_and_keeps_good_ones():
    config = build_xray_config([VLESS_WS_TLS, "not-a-valid-link://nope", SS_LINK], socks_port=11080)
    tags = [o["tag"] for o in config["outbounds"]]
    assert "proxy-0" in tags  # VLESS_WS_TLS parsed
    assert "proxy-2" in tags  # SS_LINK parsed (index 2 — the malformed one took slot 1 and was skipped)
    assert "direct" in tags
    assert config["inbounds"][0]["port"] == 11080
    assert config["routing"]["balancers"][0]["strategy"]["type"] == "leastPing"
