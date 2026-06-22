"""测试 /api/v1/body-logs 端点。"""

from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def _setup_profile(client: TestClient) -> None:
    client.put(
        "/api/v1/profile",
        json={
            "name": "测试",
            "gender": "male",
            "age": 30,
            "height_cm": 175,
            "weight_kg": 70,
            "body_fat_pct": 18,
            "target_weight_kg": 65,
            "target_date": "2026-12-31",
            "activity_level": "moderate",
        },
        headers=auth_headers(),
    )


def test_list_body_logs_empty(client: TestClient) -> None:
    resp = client.get("/api/v1/body-logs", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_and_list_body_log(client: TestClient) -> None:
    _setup_profile(client)
    payload = {
        "log_date": "2026-06-15",
        "weight_kg": 69.5,
        "body_fat_pct": 17.5,
        "note": "早上空腹",
    }
    resp = client.post("/api/v1/body-logs", json=payload, headers=auth_headers())
    assert resp.status_code == 201
    data = resp.json()
    assert data["weight_kg"] == 69.5
    assert "waist_cm" not in data

    profile_resp = client.get("/api/v1/profile", headers=auth_headers())
    assert profile_resp.json()["weight_kg"] == 69.5

    list_resp = client.get("/api/v1/body-logs", headers=auth_headers())
    assert len(list_resp.json()) == 1


def test_create_body_log_same_date(client: TestClient) -> None:
    _setup_profile(client)
    payload = {
        "log_date": "2026-06-15",
        "weight_kg": 69.0,
        "body_fat_pct": 18.0,
    }
    resp1 = client.post("/api/v1/body-logs", json=payload, headers=auth_headers())
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/body-logs", json=payload, headers=auth_headers())
    assert resp2.status_code == 409


def test_delete_body_log(client: TestClient) -> None:
    _setup_profile(client)
    resp = client.post(
        "/api/v1/body-logs",
        json={"log_date": "2026-06-14", "weight_kg": 70.0, "body_fat_pct": 18.0},
        headers=auth_headers(),
    )
    log_id = resp.json()["id"]
    resp2 = client.delete(f"/api/v1/body-logs/{log_id}", headers=auth_headers())
    assert resp2.status_code == 200

    resp3 = client.get("/api/v1/body-logs", headers=auth_headers())
    assert len(resp3.json()) == 0


def test_delete_body_log_returns_full_record(client: TestClient) -> None:
    _setup_profile(client)
    resp = client.post(
        "/api/v1/body-logs",
        json={"log_date": "2026-06-13", "weight_kg": 71.2, "body_fat_pct": 19.0},
        headers=auth_headers(),
    )
    log_id = resp.json()["id"]
    del_resp = client.delete(f"/api/v1/body-logs/{log_id}", headers=auth_headers())
    assert del_resp.status_code == 200
    body = del_resp.json()
    assert body["id"] == log_id
    assert body["log_date"] == "2026-06-13"
    assert body["weight_kg"] == 71.2
    assert body["body_fat_pct"] == 19.0


def test_list_body_logs_date_filter(client: TestClient) -> None:
    _setup_profile(client)
    for day in ("2026-06-18", "2026-06-19", "2026-06-20"):
        client.post(
            "/api/v1/body-logs",
            json={"log_date": day, "weight_kg": 70.0, "body_fat_pct": 18.0},
            headers=auth_headers(),
        )

    only_19 = client.get(
        "/api/v1/body-logs?start=2026-06-19&end=2026-06-19", headers=auth_headers()
    )
    assert len(only_19.json()) == 1
    assert only_19.json()[0]["log_date"] == "2026-06-19"

    closed = client.get(
        "/api/v1/body-logs?start=2026-06-18&end=2026-06-19", headers=auth_headers()
    )
    assert len(closed.json()) == 2

    none_match = client.get(
        "/api/v1/body-logs?start=2026-07-01", headers=auth_headers()
    )
    assert none_match.json() == []
