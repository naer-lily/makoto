"""测试 /api/v1/circumference-logs 端点。"""

from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def test_list_circumference_logs_empty(client: TestClient) -> None:
    resp = client.get("/api/v1/circumference-logs", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_and_list_circumference_log(client: TestClient) -> None:
    payload = {
        "log_date": "2026-06-15",
        "waist_cm": 80.0,
        "arm_cm": 32.0,
        "thigh_cm": 55.0,
        "note": "早上空腹",
    }
    resp = client.post(
        "/api/v1/circumference-logs", json=payload, headers=auth_headers()
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["waist_cm"] == 80.0
    assert data["arm_cm"] == 32.0
    assert data["thigh_cm"] == 55.0

    list_resp = client.get("/api/v1/circumference-logs", headers=auth_headers())
    assert len(list_resp.json()) == 1


def test_create_circumference_partial(client: TestClient) -> None:
    """部分字段为 None 也可创建。"""
    payload = {
        "log_date": "2026-06-16",
        "waist_cm": 79.5,
        "arm_cm": None,
        "thigh_cm": None,
    }
    resp = client.post(
        "/api/v1/circumference-logs", json=payload, headers=auth_headers()
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["waist_cm"] == 79.5
    assert data["arm_cm"] is None
    assert data["thigh_cm"] is None


def test_create_circumference_same_date(client: TestClient) -> None:
    payload = {"log_date": "2026-06-15", "waist_cm": 80.0}
    resp1 = client.post(
        "/api/v1/circumference-logs", json=payload, headers=auth_headers()
    )
    assert resp1.status_code == 201

    resp2 = client.post(
        "/api/v1/circumference-logs", json=payload, headers=auth_headers()
    )
    assert resp2.status_code == 409


def test_delete_circumference_log(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/circumference-logs",
        json={"log_date": "2026-06-14", "waist_cm": 81.0},
        headers=auth_headers(),
    )
    log_id = resp.json()["id"]
    resp2 = client.delete(
        f"/api/v1/circumference-logs/{log_id}", headers=auth_headers()
    )
    assert resp2.status_code == 200

    resp3 = client.get("/api/v1/circumference-logs", headers=auth_headers())
    assert len(resp3.json()) == 0


def test_delete_circumference_log_returns_full_record(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/circumference-logs",
        json={"log_date": "2026-06-13", "waist_cm": 82.0, "arm_cm": 33.0},
        headers=auth_headers(),
    )
    log_id = resp.json()["id"]
    del_resp = client.delete(
        f"/api/v1/circumference-logs/{log_id}", headers=auth_headers()
    )
    assert del_resp.status_code == 200
    body = del_resp.json()
    assert body["id"] == log_id
    assert body["log_date"] == "2026-06-13"
    assert body["waist_cm"] == 82.0
    assert body["arm_cm"] == 33.0


def test_list_circumference_logs_date_filter(client: TestClient) -> None:
    for day in ("2026-06-18", "2026-06-19", "2026-06-20"):
        client.post(
            "/api/v1/circumference-logs",
            json={"log_date": day, "waist_cm": 80.0},
            headers=auth_headers(),
        )

    only_19 = client.get(
        "/api/v1/circumference-logs?start=2026-06-19&end=2026-06-19",
        headers=auth_headers(),
    )
    assert len(only_19.json()) == 1
    assert only_19.json()[0]["log_date"] == "2026-06-19"

    closed = client.get(
        "/api/v1/circumference-logs?start=2026-06-18&end=2026-06-19",
        headers=auth_headers(),
    )
    assert len(closed.json()) == 2

    none_match = client.get(
        "/api/v1/circumference-logs?start=2026-07-01", headers=auth_headers()
    )
    assert none_match.json() == []
