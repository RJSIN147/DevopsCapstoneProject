def test_root_reports_service_name(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["service"] == "ClinicDesk API"


def test_health_is_up(client):
    assert client.get("/health").json() == {"status": "UP"}


def test_ready_checks_database(client):
    res = client.get("/ready")
    assert res.status_code == 200
    assert res.json()["status"] == "READY"


def test_metrics_endpoint_is_prometheus_format(client):
    client.get("/api/doctors")
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "http_requests_total" in res.text
    assert "clinicdesk_appointments_booked_total" in res.text
