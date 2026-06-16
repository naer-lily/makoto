"""测试 /api/v1/foods 端点。"""

from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def test_list_foods_empty(client: TestClient) -> None:
    resp = client.get("/api/v1/foods", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json() == []


def test_add_food(client: TestClient) -> None:
    payload = {
        "name": "鸡胸肉",
        "calories_per_100g": 133.0,
        "protein_per_100g": 31.0,
        "carbs_per_100g": 0.0,
        "fat_per_100g": 1.2,
    }
    resp = client.post("/api/v1/foods", json=payload, headers=auth_headers())
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "鸡胸肉"
    assert data["id"] > 0
    assert "created_at" in data


def test_add_food_duplicate(client: TestClient) -> None:
    payload = {"name": "米饭", "calories_per_100g": 116}
    resp1 = client.post("/api/v1/foods", json=payload, headers=auth_headers())
    assert resp1.status_code == 201
    resp2 = client.post("/api/v1/foods", json=payload, headers=auth_headers())
    assert resp2.status_code == 409


def test_list_foods_after_add(client: TestClient) -> None:
    client.post(
        "/api/v1/foods",
        json={"name": "苹果", "calories_per_100g": 52},
        headers=auth_headers(),
    )
    resp = client.get("/api/v1/foods", headers=auth_headers())
    assert resp.status_code == 200
    foods = resp.json()
    assert len(foods) >= 1
    assert any(f["name"] == "苹果" for f in foods)


def test_get_food_by_id(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/foods",
        json={"name": "全麦面包", "calories_per_100g": 246},
        headers=auth_headers(),
    )
    food_id = resp.json()["id"]
    resp2 = client.get(f"/api/v1/foods/{food_id}", headers=auth_headers())
    assert resp2.status_code == 200
    assert resp2.json()["name"] == "全麦面包"


def test_get_food_not_found(client: TestClient) -> None:
    resp = client.get("/api/v1/foods/99999", headers=auth_headers())
    assert resp.status_code == 404


def test_search_food(client: TestClient) -> None:
    client.post(
        "/api/v1/foods",
        json={"name": "牛肉", "search_keywords": ["牛排", "beef"]},
        headers=auth_headers(),
    )
    client.post(
        "/api/v1/foods",
        json={"name": "猪肉", "search_keywords": ["排骨", "pork"]},
        headers=auth_headers(),
    )

    resp = client.get(
        "/api/v1/foods/search?q=牛&limit=5", headers=auth_headers()
    )
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert results[0]["name"] == "牛肉"

    resp2 = client.get(
        "/api/v1/foods/search?q=beef&limit=5", headers=auth_headers()
    )
    assert resp2.status_code == 200
    assert len(resp2.json()) >= 1


def test_delete_food(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/foods",
        json={"name": "西瓜"},
        headers=auth_headers(),
    )
    food_id = resp.json()["id"]
    resp2 = client.delete(f"/api/v1/foods/{food_id}", headers=auth_headers())
    assert resp2.status_code == 200

    resp3 = client.get(f"/api/v1/foods/{food_id}", headers=auth_headers())
    assert resp3.status_code == 404


def test_update_food(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/foods",
        json={"name": "牛奶", "calories_per_100g": 42},
        headers=auth_headers(),
    )
    food_id = resp.json()["id"]

    payload = {
        "name": "全脂牛奶",
        "calories_per_100g": 61.0,
        "protein_per_100g": 3.2,
        "carbs_per_100g": 4.8,
        "fat_per_100g": 3.3,
    }
    resp2 = client.put(
        f"/api/v1/foods/{food_id}", json=payload, headers=auth_headers()
    )
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["name"] == "全脂牛奶"
    assert data["calories_per_100g"] == 61.0
    assert data["protein_per_100g"] == 3.2


def test_update_food_not_found(client: TestClient) -> None:
    resp = client.put(
        "/api/v1/foods/99999",
        json={"name": "不存在"},
        headers=auth_headers(),
    )
    assert resp.status_code == 404


def test_update_food_name_cascade(client: TestClient) -> None:
    """改名食物应同步更新饮食记录中的 food_name。"""
    resp = client.post(
        "/api/v1/foods",
        json={"name": "糙米", "calories_per_100g": 111},
        headers=auth_headers(),
    )
    food_id = resp.json()["id"]

    client.post(
        "/api/v1/diet-logs",
        json={
            "log_time": "2026-06-15T12:00:00",
            "food_name": "糙米",
            "grams": 100,
        },
        headers=auth_headers(),
    )

    client.put(
        f"/api/v1/foods/{food_id}",
        json={"name": "发芽糙米", "calories_per_100g": 111},
        headers=auth_headers(),
    )

    diet_resp = client.get("/api/v1/diet-logs", headers=auth_headers())
    diets = diet_resp.json()
    assert len(diets) == 1
    assert diets[0]["food_name"] == "发芽糙米"


def test_delete_food_with_diet_refs(client: TestClient) -> None:
    """删除被饮食记录引用的食物时应返回 409。"""
    resp = client.post(
        "/api/v1/foods",
        json={"name": "三文鱼", "calories_per_100g": 208},
        headers=auth_headers(),
    )
    food_id = resp.json()["id"]

    client.post(
        "/api/v1/diet-logs",
        json={
            "log_time": "2026-06-15T12:01:00",
            "food_name": "三文鱼",
            "grams": 150,
        },
        headers=auth_headers(),
    )

    resp2 = client.delete(f"/api/v1/foods/{food_id}", headers=auth_headers())
    assert resp2.status_code == 409
