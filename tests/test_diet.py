"""测试 /api/v1/diet-logs 端点。"""


from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def _setup_food(client: TestClient) -> None:
    client.post(
        "/api/v1/foods",
        json={"name": "鸡胸肉", "calories_per_100g": 133, "protein_per_100g": 31},
        headers=auth_headers(),
    )


def test_list_diet_logs_empty(client: TestClient) -> None:
    resp = client.get("/api/v1/diet-logs", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_and_read_diet_log(client: TestClient) -> None:
    _setup_food(client)
    payload = {
        "log_time": "2026-06-15T12:30:00",
        "food_name": "鸡胸肉",
        "grams": 200.0,
    }
    resp = client.post("/api/v1/diet-logs", json=payload, headers=auth_headers())
    assert resp.status_code == 201
    data = resp.json()
    assert data["food_name"] == "鸡胸肉"
    assert data["grams"] == 200.0
    assert data["calories_kcal"] == 266.0  # 133 * 2
    assert data["protein_g"] == 62.0  # 31 * 2

    list_resp = client.get("/api/v1/diet-logs", headers=auth_headers())
    assert len(list_resp.json()) == 1


def test_create_diet_log_duplicate_time(client: TestClient) -> None:
    _setup_food(client)
    payload = {
        "log_time": "2026-06-15T12:00:00",
        "food_name": "鸡胸肉",
        "grams": 100.0,
    }
    resp1 = client.post("/api/v1/diet-logs", json=payload, headers=auth_headers())
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/diet-logs", json=payload, headers=auth_headers())
    assert resp2.status_code == 409


def test_create_diet_log_food_not_found(client: TestClient) -> None:
    payload = {
        "log_time": "2026-06-15T12:00:00",
        "food_name": "不存在食物",
        "grams": 100.0,
    }
    resp = client.post("/api/v1/diet-logs", json=payload, headers=auth_headers())
    assert resp.status_code == 404


def test_delete_diet_log(client: TestClient) -> None:
    _setup_food(client)
    resp = client.post(
        "/api/v1/diet-logs",
        json={"log_time": "2026-06-14T18:00:00", "food_name": "鸡胸肉", "grams": 150},
        headers=auth_headers(),
    )
    log_id = resp.json()["id"]
    resp2 = client.delete(f"/api/v1/diet-logs/{log_id}", headers=auth_headers())
    assert resp2.status_code == 200

    resp3 = client.get("/api/v1/diet-logs", headers=auth_headers())
    assert len(resp3.json()) == 0
