def _create_order(client, desired_count=50):
    resp = client.post("/api/v1/orders/", json={
        "target_link": "https://t.me/test_target",
        "source_links": ["https://t.me/test_source"],
        "desired_count": desired_count,
    })
    assert resp.status_code == 200
    return resp.json()["order_id"]


def test_create_and_list_order(authed_client):
    order_id = _create_order(authed_client)
    orders = authed_client.get("/api/v1/orders/").json()
    assert any(o["id"] == order_id for o in orders)


def test_action_pause_resume_cancel(authed_client):
    order_id = _create_order(authed_client)

    pause = authed_client.post(f"/api/v1/orders/{order_id}/action", json={"type": "pause"})
    assert pause.json()["new_status"] == "paused"

    resume = authed_client.post(f"/api/v1/orders/{order_id}/action", json={"type": "resume"})
    assert resume.json()["new_status"] == "in_progress"

    cancel = authed_client.post(f"/api/v1/orders/{order_id}/action", json={"type": "cancel"})
    assert cancel.json()["new_status"] == "cancelled"


def test_action_rejects_unknown_type(authed_client):
    order_id = _create_order(authed_client)
    resp = authed_client.post(f"/api/v1/orders/{order_id}/action", json={"type": "explode"})
    assert resp.status_code == 400


def test_delete_blocked_while_order_is_active(authed_client):
    order_id = _create_order(authed_client)  # starts PENDING_AGENT
    resp = authed_client.delete(f"/api/v1/orders/{order_id}")
    assert resp.status_code == 400

    orders = authed_client.get("/api/v1/orders/").json()
    assert any(o["id"] == order_id for o in orders)  # still there


def test_delete_allowed_after_cancel(authed_client):
    order_id = _create_order(authed_client)
    authed_client.post(f"/api/v1/orders/{order_id}/action", json={"type": "cancel"})

    resp = authed_client.delete(f"/api/v1/orders/{order_id}")
    assert resp.status_code == 200

    orders = authed_client.get("/api/v1/orders/").json()
    assert not any(o["id"] == order_id for o in orders)


def test_orders_endpoint_requires_auth(client):
    resp = client.get("/api/v1/orders/")
    assert resp.status_code == 401
