def test_health_is_public_and_reports_database_ok(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["api"] == "ok"
    assert data["database"] == "ok"
    assert data["worker"] in ("ok", "stale", "unknown")
    assert "telegram_reachable" in data


def test_health_reflects_worker_heartbeat(client, db_session):
    from app.services import health

    health.record_worker_heartbeat(db_session)
    resp = client.get("/api/v1/health")
    assert resp.json()["worker"] == "ok"
