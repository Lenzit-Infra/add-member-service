from app.core import security
from app.models.user import User


def _claim(client, email="admin@example.com", username="boss", password="supersecret1"):
    token = security.create_claim_token(email)
    return client.post("/api/v1/account/claim-admin/complete", json={
        "token": token, "username": username, "password": password,
    })


def test_claim_request_never_leaks_eligibility(client):
    # Same generic response whether the email is eligible or not — no account enumeration.
    eligible = client.post("/api/v1/account/claim-admin/request", json={"email": "admin@example.com"})
    not_eligible = client.post("/api/v1/account/claim-admin/request", json={"email": "stranger@example.com"})
    assert eligible.status_code == 200
    assert not_eligible.status_code == 200
    assert eligible.json() == not_eligible.json()


def test_claim_complete_rejects_email_not_in_allowlist(client):
    token = security.create_claim_token("stranger@example.com")
    resp = client.post("/api/v1/account/claim-admin/complete", json={
        "token": token, "username": "intruder", "password": "supersecret1",
    })
    assert resp.status_code == 403


def test_claim_complete_succeeds_for_allowlisted_email(client):
    resp = _claim(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["email"] == "admin@example.com"
    assert "access_token" in body


def test_claim_cannot_be_replayed_after_account_exists(client):
    first = _claim(client)
    assert first.status_code == 200

    # A second, freshly-signed claim token for the same email must still be rejected —
    # eligibility requires "no existing account", not just allowlist membership.
    second = _claim(client, username="someoneelse")
    assert second.status_code == 409


def test_claim_token_for_wrong_token_type_rejected(client):
    # A reset token must not work as a claim token, even though both are signed with the same secret.
    fake_reset_token = security.create_reset_token(user_id=1, token_version=0)
    resp = client.post("/api/v1/account/claim-admin/complete", json={
        "token": fake_reset_token, "username": "boss", "password": "supersecret1",
    })
    assert resp.status_code == 400


def test_login_success_then_failure_lockout(client):
    _claim(client, password="correct-password1")

    for _ in range(5):
        resp = client.post("/api/v1/account/login", json={
            "username_or_email": "boss", "password": "wrong-password",
        })
        assert resp.status_code == 401

    # 6th attempt: account should now be locked regardless of password correctness.
    locked = client.post("/api/v1/account/login", json={
        "username_or_email": "boss", "password": "correct-password1",
    })
    assert locked.status_code == 423


def test_login_success_sets_refresh_cookie_and_returns_access_token(client):
    _claim(client, password="correct-password1")
    resp = client.post("/api/v1/account/login", json={
        "username_or_email": "boss", "password": "correct-password1",
    })
    assert resp.status_code == 200
    assert "refresh_token" in resp.cookies
    assert resp.json()["user"]["username"] == "boss"


def test_refresh_uses_cookie_to_issue_new_access_token(client):
    _claim(client, password="correct-password1")
    client.post("/api/v1/account/login", json={"username_or_email": "boss", "password": "correct-password1"})

    resp = client.post("/api/v1/account/refresh")
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_reset_password_invalidates_existing_sessions(client, db_session):
    _claim(client, password="old-password1")
    login_resp = client.post("/api/v1/account/login", json={"username_or_email": "boss", "password": "old-password1"})
    assert login_resp.status_code == 200

    # Refresh works before reset.
    assert client.post("/api/v1/account/refresh").status_code == 200

    user = db_session.query(User).filter(User.username == "boss").first()
    reset_token = security.create_reset_token(user.id, user.token_version)
    reset_resp = client.post("/api/v1/account/reset-password", json={
        "token": reset_token, "new_password": "brand-new-password1",
    })
    assert reset_resp.status_code == 200

    # The OLD refresh cookie (issued before reset) must now be rejected — token_version moved on.
    stale_refresh = client.post("/api/v1/account/refresh")
    assert stale_refresh.status_code == 401

    # New password works.
    relogin = client.post("/api/v1/account/login", json={"username_or_email": "boss", "password": "brand-new-password1"})
    assert relogin.status_code == 200


def test_protected_routes_require_authentication(client):
    resp = client.get("/api/v1/analytics/summary")
    assert resp.status_code == 401


def test_protected_routes_work_with_valid_access_token(client):
    _claim(client, password="correct-password1")
    login_resp = client.post("/api/v1/account/login", json={"username_or_email": "boss", "password": "correct-password1"})
    access_token = login_resp.json()["access_token"]

    resp = client.get("/api/v1/analytics/summary", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 200
