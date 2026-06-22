"""测试 /api/v1/keep 端点。"""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def _setup_profile(client: TestClient, keep_token: str | None = None) -> None:
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
            "keep_token": keep_token,
        },
        headers=auth_headers(),
    )


def test_keep_without_profile(client: TestClient) -> None:
    """未设画像时返回 404。"""
    resp = client.get("/api/v1/keep/fitness", headers=auth_headers())
    assert resp.status_code == 404


def test_keep_without_token(client: TestClient) -> None:
    """未配置 keep_token 时返回空列表。"""
    _setup_profile(client, keep_token=None)
    resp = client.get("/api/v1/keep/fitness", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json() == []


def test_weekly_load_without_token(client: TestClient) -> None:
    """未配置 keep_token 时周负荷也返回空列表。"""
    _setup_profile(client, keep_token=None)
    resp = client.get("/api/v1/keep/weekly-load", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.slow
def test_fitness_with_real_token(client: TestClient) -> None:
    """使用内嵌 Keep token 验证体能水平接口返回真实数据。"""
    from makoto.server.keep_client import TOKEN

    _setup_profile(client, keep_token=TOKEN)
    resp = client.get("/api/v1/keep/fitness", headers=auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0, "fitness 应返回至少一条记录"
    first = data[0]
    assert "date" in first
    assert "atl" in first
    assert "ctl" in first
    assert "tsb" in first
    assert isinstance(first["atl"], (int, float))
    assert isinstance(first["ctl"], (int, float))
    assert isinstance(first["tsb"], (int, float))


@pytest.mark.slow
def test_weekly_load_with_real_token(client: TestClient) -> None:
    """使用内嵌 Keep token 验证周运动负荷接口返回真实数据。"""
    from makoto.server.keep_client import TOKEN

    _setup_profile(client, keep_token=TOKEN)
    resp = client.get("/api/v1/keep/weekly-load", headers=auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0, "weekly-load 应返回至少一条记录"
    first = data[0]
    assert "user_id" in first
    assert "week_start" in first
    assert "load_lower" in first
    assert "load_upper" in first
    assert isinstance(first["load_lower"], (int, float))
    assert isinstance(first["load_upper"], (int, float))
