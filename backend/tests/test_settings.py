from app.core import security


def _claim(client, email="second@example.com", username="secondadmin", password="supersecret1"):
    token = security.create_claim_token(email)
    return client.post("/api/v1/account/claim-admin/complete", json={
        "token": token, "username": username, "password": password,
    })


def test_get_settings_returns_schema_enriched_values(authed_client):
    resp = authed_client.get("/api/v1/analytics/settings")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list) and len(body) > 0
    keys = {s["key"] for s in body}
    assert "daily_limit_per_agent" in keys
    assert "login_max_failed_attempts" in keys

    entry = next(s for s in body if s["key"] == "daily_limit_per_agent")
    assert entry["category"] == "Anti-Ban / Telegram Safety"
    assert entry["value"] == "30"


def test_update_setting_changes_value(authed_client):
    authed_client.post("/api/v1/analytics/settings", json={"key": "batch_size", "value": "7"})
    resp = authed_client.get("/api/v1/analytics/settings")
    entry = next(s for s in resp.json() if s["key"] == "batch_size")
    assert entry["value"] == "7"


def test_admin_emails_seeded_from_env_on_first_call(authed_client):
    resp = authed_client.get("/api/v1/analytics/admin-emails")
    assert resp.status_code == 200
    assert resp.json()["emails"] == ["admin@example.com"]  # from config.ADMIN_EMAILS in conftest


def test_add_and_remove_admin_email(authed_client):
    add_resp = authed_client.post("/api/v1/analytics/admin-emails", json={"email": "second@example.com"})
    assert add_resp.status_code == 200
    assert "second@example.com" in add_resp.json()["emails"]

    remove_resp = authed_client.delete("/api/v1/analytics/admin-emails/second@example.com")
    assert remove_resp.status_code == 200
    assert "second@example.com" not in remove_resp.json()["emails"]


def test_cannot_remove_the_last_admin_email(authed_client):
    # Only admin@example.com exists at this point (seeded from config).
    resp = authed_client.delete("/api/v1/analytics/admin-emails/admin@example.com")
    assert resp.status_code == 400


def test_claim_eligibility_follows_live_admin_emails_list_not_env(authed_client, client):
    # second@example.com is NOT in config.ADMIN_EMAILS — only reachable by being added live.
    not_yet_eligible = client.post("/api/v1/account/claim-admin/request", json={"email": "second@example.com"})
    assert not_yet_eligible.status_code == 200  # generic response either way, no leak

    authed_client.post("/api/v1/analytics/admin-emails", json={"email": "second@example.com"})

    claim_resp = _claim(client)
    assert claim_resp.status_code == 200
    assert claim_resp.json()["user"]["email"] == "second@example.com"
