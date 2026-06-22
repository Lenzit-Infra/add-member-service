from app.models.user import User


def _create_order(client, desired_count=50):
    resp = client.post("/api/v1/orders/", json={
        "target_link": "https://t.me/test_target",
        "source_links": ["https://t.me/test_source"],
        "desired_count": desired_count,
    })
    assert resp.status_code == 200
    return resp.json()["order_id"]


def test_admin_can_manage_settings(authed_client):
    resp = authed_client.post("/api/v1/analytics/settings", json={"key": "batch_size", "value": "9"})
    assert resp.status_code == 200


def test_operator_default_permissions_allow_orders_and_agents(authed_client, role_client):
    order_id = _create_order(authed_client)

    operator = role_client("operator")
    resp = operator.post(f"/api/v1/orders/{order_id}/action", json={"type": "pause"})
    assert resp.status_code == 200


def test_operator_cannot_manage_settings_by_default(role_client):
    operator = role_client("operator")
    resp = operator.post("/api/v1/analytics/settings", json={"key": "batch_size", "value": "9"})
    assert resp.status_code == 403


def test_viewer_cannot_manage_orders_or_agents(authed_client, role_client):
    order_id = _create_order(authed_client)

    viewer = role_client("viewer")
    resp = viewer.post(f"/api/v1/orders/{order_id}/action", json={"type": "pause"})
    assert resp.status_code == 403


def test_viewer_can_still_view(role_client):
    viewer = role_client("viewer")
    resp = viewer.get("/api/v1/orders/")
    assert resp.status_code == 200


def test_fixed_admin_only_permissions_block_operator_even_if_granted_everything_else(authed_client, role_client):
    # Grant operator every configurable permission — admin_emails.manage / users.manage / roles.manage
    # are FIXED admin-only and must stay blocked regardless.
    authed_client.post("/api/v1/account/roles/operator/permissions", json={"permissions": ["orders.manage", "agents.manage", "settings.manage"]})

    operator = role_client("operator")
    assert operator.get("/api/v1/account/users").status_code == 403
    assert operator.get("/api/v1/analytics/admin-emails").status_code == 403
    assert operator.get("/api/v1/account/roles").status_code == 403


def test_role_permissions_update_changes_enforcement_live(authed_client, role_client):
    order_id = _create_order(authed_client)
    operator = role_client("operator")

    # Default: operator can pause orders.
    assert operator.post(f"/api/v1/orders/{order_id}/action", json={"type": "resume"}).status_code == 200

    # Admin revokes orders.manage from operator.
    resp = authed_client.post("/api/v1/account/roles/operator/permissions", json={"permissions": ["agents.manage"]})
    assert resp.status_code == 200

    assert operator.post(f"/api/v1/orders/{order_id}/action", json={"type": "pause"}).status_code == 403


def test_cannot_edit_admin_role_permissions(authed_client):
    resp = authed_client.post("/api/v1/account/roles/admin/permissions", json={"permissions": []})
    assert resp.status_code == 400


def test_create_user_via_api_and_list(authed_client):
    resp = authed_client.post("/api/v1/account/users", json={
        "username": "newop", "email": "newop@example.com", "password": "supersecret1", "role": "operator",
    })
    assert resp.status_code == 200
    assert resp.json()["role"] == "operator"

    listed = authed_client.get("/api/v1/account/users").json()
    assert any(u["username"] == "newop" for u in listed)


def test_cannot_demote_the_last_remaining_admin(authed_client):
    create = authed_client.post("/api/v1/account/users", json={
        "username": "soleadmin", "email": "soleadmin@example.com", "password": "supersecret1", "role": "admin",
    })
    user_id = create.json()["id"]

    # soleadmin is the only PERSISTED admin (authed_client's dummy admin isn't a real row) — demoting it must be blocked.
    resp = authed_client.patch(f"/api/v1/account/users/{user_id}", json={"role": "operator"})
    assert resp.status_code == 400


def test_cannot_delete_self(authed_client, role_client):
    create = authed_client.post("/api/v1/account/users", json={
        "username": "selfdelete", "email": "selfdelete@example.com", "password": "supersecret1", "role": "admin",
    })
    user_id = create.json()["id"]

    # Now act AS that exact user (same id) and try to delete it — must be blocked regardless of role.
    as_self = role_client("admin", user_id=user_id)
    resp = as_self.delete(f"/api/v1/account/users/{user_id}")
    assert resp.status_code == 400


def test_mutating_action_writes_audit_log(authed_client):
    authed_client.post("/api/v1/analytics/settings", json={"key": "batch_size", "value": "12"})
    log = authed_client.get("/api/v1/account/audit-log").json()
    assert any(entry["action"] == "settings.update" for entry in log)


def test_login_records_client_ip(client, db_session):
    from app.core import security
    token = security.create_claim_token("admin@example.com")
    client.post("/api/v1/account/claim-admin/complete", json={
        "token": token, "username": "ipcheck", "password": "supersecret1",
    })
    resp = client.post(
        "/api/v1/account/login",
        json={"username_or_email": "ipcheck", "password": "supersecret1"},
        headers={"CF-Connecting-IP": "203.0.113.5"},
    )
    assert resp.status_code == 200

    user = db_session.query(User).filter(User.username == "ipcheck").first()
    assert user.last_login_ip == "203.0.113.5"
