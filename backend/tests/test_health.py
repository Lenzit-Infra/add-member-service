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


def test_classify_status_down_when_no_response():
    from app.services.health import classify_status

    status, issues = classify_status(None)
    assert status == "down"
    assert issues


def test_classify_status_ok_when_everything_fine():
    from app.services.health import classify_status

    status, issues = classify_status({"database": "ok", "worker": "ok", "telegram_reachable": True})
    assert status == "ok"
    assert issues == []


def test_classify_status_degraded_lists_each_issue():
    from app.services.health import classify_status

    status, issues = classify_status({"database": "error", "worker": "stale", "telegram_reachable": False})
    assert status == "degraded"
    assert len(issues) == 3
