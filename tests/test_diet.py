"""测试 /api/v1/diet-logs 端点。"""


from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def _setup_food(client: TestClient) -> int:
    resp = client.post(
        "/api/v1/foods",
        json={"name": "鸡胸肉", "calories_per_100g": 133, "protein_per_100g": 31},
        headers=auth_headers(),
    )
    return int(resp.json()["id"])


def test_list_diet_logs_empty(client: TestClient) -> None:
    resp = client.get("/api/v1/diet-logs", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_and_read_diet_log(client: TestClient) -> None:
    food_id = _setup_food(client)
    payload = {
        "log_time": "2026-06-15T12:30:00",
        "food_id": food_id,
        "grams": 200.0,
    }
    resp = client.post("/api/v1/diet-logs", json=payload, headers=auth_headers())
    assert resp.status_code == 201
    data = resp.json()
    assert data["food_id"] == food_id
    assert data["food_name"] == "鸡胸肉"
    assert data["grams"] == 200.0
    assert data["calories_kcal"] == 266.0  # 133 * 2
    assert data["protein_g"] == 62.0  # 31 * 2

    list_resp = client.get("/api/v1/diet-logs", headers=auth_headers())
    assert len(list_resp.json()) == 1


def test_create_diet_log_duplicate_time(client: TestClient) -> None:
    food_id = _setup_food(client)
    payload = {
        "log_time": "2026-06-15T12:00:00",
        "food_id": food_id,
        "grams": 100.0,
    }
    resp1 = client.post("/api/v1/diet-logs", json=payload, headers=auth_headers())
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/diet-logs", json=payload, headers=auth_headers())
    assert resp2.status_code == 409


def test_create_diet_log_food_not_found(client: TestClient) -> None:
    payload = {
        "log_time": "2026-06-15T12:00:00",
        "food_id": 99999,
        "grams": 100.0,
    }
    resp = client.post("/api/v1/diet-logs", json=payload, headers=auth_headers())
    assert resp.status_code == 404


def test_delete_diet_log(client: TestClient) -> None:
    food_id = _setup_food(client)
    resp = client.post(
        "/api/v1/diet-logs",
        json={"log_time": "2026-06-14T18:00:00", "food_id": food_id, "grams": 150},
        headers=auth_headers(),
    )
    log_id = resp.json()["id"]
    resp2 = client.delete(f"/api/v1/diet-logs/{log_id}", headers=auth_headers())
    assert resp2.status_code == 200

    resp3 = client.get("/api/v1/diet-logs", headers=auth_headers())
    assert len(resp3.json()) == 0


def test_update_diet_log(client: TestClient) -> None:
    food_id = _setup_food(client)
    resp = client.post(
        "/api/v1/diet-logs",
        json={"log_time": "2026-06-15T12:00:00", "food_id": food_id, "grams": 100},
        headers=auth_headers(),
    )
    log_id = resp.json()["id"]

    payload = {
        "log_time": "2026-06-15T13:00:00",
        "food_id": food_id,
        "grams": 200,
    }
    resp2 = client.put(
        f"/api/v1/diet-logs/{log_id}", json=payload, headers=auth_headers()
    )
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["grams"] == 200.0
    assert data["calories_kcal"] == 266.0


def test_update_diet_log_not_found(client: TestClient) -> None:
    food_id = _setup_food(client)
    resp = client.put(
        "/api/v1/diet-logs/99999",
        json={
            "log_time": "2026-06-15T12:00:00",
            "food_id": food_id,
            "grams": 100,
        },
        headers=auth_headers(),
    )
    assert resp.status_code == 404


def test_update_diet_log_duplicate_time(client: TestClient) -> None:
    food_id = _setup_food(client)
    _r1 = client.post(
        "/api/v1/diet-logs",
        json={"log_time": "2026-06-15T14:00:00", "food_id": food_id, "grams": 100},
        headers=auth_headers(),
    )
    r2 = client.post(
        "/api/v1/diet-logs",
        json={"log_time": "2026-06-15T15:00:00", "food_id": food_id, "grams": 150},
        headers=auth_headers(),
    )

    resp = client.put(
        f"/api/v1/diet-logs/{r2.json()['id']}",
        json={
            "log_time": "2026-06-15T14:00:00",
            "food_id": food_id,
            "grams": 150,
        },
        headers=auth_headers(),
    )
    assert resp.status_code == 409


def test_diet_log_includes_food_base_nutrition(client: TestClient) -> None:
    food_id = _setup_food(client)
    resp = client.post(
        "/api/v1/diet-logs",
        json={"log_time": "2026-06-15T12:30:00", "food_id": food_id, "grams": 200},
        headers=auth_headers(),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["food_calories_per_100g"] == 133.0
    assert data["food_protein_per_100g"] == 31.0
    assert data["food_carbs_per_100g"] == 0.0
    assert data["food_fat_per_100g"] == 0.0


def test_delete_diet_log_returns_full_record(client: TestClient) -> None:
    food_id = _setup_food(client)
    resp = client.post(
        "/api/v1/diet-logs",
        json={"log_time": "2026-06-14T18:00:00", "food_id": food_id, "grams": 150},
        headers=auth_headers(),
    )
    log_id = resp.json()["id"]
    del_resp = client.delete(f"/api/v1/diet-logs/{log_id}", headers=auth_headers())
    assert del_resp.status_code == 200
    body = del_resp.json()
    assert body["id"] == log_id
    assert body["food_id"] == food_id
    assert body["food_name"] == "鸡胸肉"
    assert body["grams"] == 150.0
    assert body["calories_kcal"] == 199.5  # 133 * 1.5
    assert body["food_calories_per_100g"] == 133.0


def test_list_diet_logs_date_filter(client: TestClient) -> None:
    food_id = _setup_food(client)
    for day in ("2026-06-18", "2026-06-19", "2026-06-20"):
        client.post(
            "/api/v1/diet-logs",
            json={
                "log_time": f"{day}T08:00:00",
                "food_id": food_id,
                "grams": 100,
            },
            headers=auth_headers(),
        )

    only_19 = client.get(
        "/api/v1/diet-logs?start=2026-06-19&end=2026-06-19", headers=auth_headers()
    )
    assert only_19.status_code == 200
    rows = only_19.json()
    assert len(rows) == 1
    assert rows[0]["log_time"].startswith("2026-06-19")

    closed_range = client.get(
        "/api/v1/diet-logs?start=2026-06-18&end=2026-06-19", headers=auth_headers()
    )
    assert len(closed_range.json()) == 2  # 前闭后闭含两端

    from_19 = client.get("/api/v1/diet-logs?start=2026-06-19", headers=auth_headers())
    assert len(from_19.json()) == 2  # 19、20

    until_19 = client.get("/api/v1/diet-logs?end=2026-06-19", headers=auth_headers())
    assert len(until_19.json()) == 2  # 18、19

    none_match = client.get(
        "/api/v1/diet-logs?start=2026-07-01", headers=auth_headers()
    )
    assert none_match.json() == []
