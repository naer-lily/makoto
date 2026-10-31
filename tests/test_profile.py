"""测试 /api/v1/profile 端点（不再要求 BIA 体脂，不返回 FFM）。"""

from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def test_get_profile_404_when_not_set(client: TestClient) -> None:
    resp = client.get("/api/v1/profile", headers=auth_headers())
    assert resp.status_code == 404


def test_set_and_get_profile_without_body_fat(client: TestClient) -> None:
    payload = {
        "name": "测试用户",
        "gender": "male",
        "age": 30,
        "height_cm": 175.0,
        "weight_kg": 70.0,
        "target_weight_kg": 65.0,
        "target_date": "2026-12-31",
        "activity_level": "moderate",
    }
    resp = client.put("/api/v1/profile", json=payload, headers=auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "测试用户"
    assert data["weight_kg"] == 70.0
    assert data["body_fat_pct"] is None
    assert data["ffm_kg"] is None
    assert data["bmr_kcal"] > 0
    assert data["netee_kcal"] > 0
    assert data["days_remaining"] > 0


def test_set_profile_stores_home_scale_body_fat(client: TestClient) -> None:
    """家秤体脂应保存；FFM 由它推算，健身房 BIA 机数据不进画像。"""
    payload = {
        "name": "测试用户",
        "gender": "female",
        "age": 25,
        "height_cm": 160.0,
        "weight_kg": 55.0,
        "body_fat_pct": 22.0,
        "target_weight_kg": 50.0,
        "target_date": "2026-12-31",
        "activity_level": "light",
    }
    resp = client.put("/api/v1/profile", json=payload, headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json()["body_fat_pct"] == 22.0
    assert resp.json()["ffm_kg"] == 42.9


def test_update_profile(client: TestClient) -> None:
    payload = {
        "name": "测试用户",
        "gender": "female",
        "age": 25,
        "height_cm": 160.0,
        "weight_kg": 55.0,
        "body_fat_pct": 22.0,
        "target_weight_kg": 50.0,
        "target_date": "2026-12-31",
        "activity_level": "light",
    }
    resp1 = client.put("/api/v1/profile", json=payload, headers=auth_headers())
    assert resp1.status_code == 200
    assert resp1.json()["weight_kg"] == 55.0

    payload["weight_kg"] = 54.0
    resp2 = client.put("/api/v1/profile", json=payload, headers=auth_headers())
    assert resp2.status_code == 200
    assert resp2.json()["weight_kg"] == 54.0
    assert resp2.json()["body_fat_pct"] == 22.0
    assert resp2.json()["ffm_kg"] == 42.1
