"""测试 /api/v1/weather 端点。"""

from __future__ import annotations

from unittest.mock import AsyncMock
from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.conftest import auth_headers

_MOCK_FORECAST_JSON = (
    '{"daily":{'
    '"time":["2026-07-17","2026-07-18"],'
    '"temperature_2m_max":[35.2,33.8],'
    '"temperature_2m_min":[26.1,25.3],'
    '"precipitation_sum":[0.0,2.3],'
    '"precipitation_probability_max":[5,45],'
    '"weathercode":[3,80]}}'
)


def test_list_watches_empty(client: TestClient) -> None:
    resp = client.get("/api/v1/weather/watches", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_watch(client: TestClient) -> None:
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.text = _MOCK_FORECAST_JSON
        mock_get.return_value.raise_for_status = lambda: None

        payload = {"label": "北京", "latitude": 39.906, "longitude": 116.391}
        resp = client.post("/api/v1/weather/watches", json=payload, headers=auth_headers())
        assert resp.status_code == 201
        data = resp.json()
        assert data["label"] == "北京"
        assert data["latitude"] == 39.906
        assert data["longitude"] == 116.391
        assert data["id"] > 0
        assert "created_at" in data


def test_create_watch_duplicate(client: TestClient) -> None:
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.text = _MOCK_FORECAST_JSON
        mock_get.return_value.raise_for_status = lambda: None

        payload = {"label": "上海", "latitude": 31.23, "longitude": 121.47}
        resp1 = client.post("/api/v1/weather/watches", json=payload, headers=auth_headers())
        assert resp1.status_code == 201
        resp2 = client.post("/api/v1/weather/watches", json=payload, headers=auth_headers())
        assert resp2.status_code == 409


def test_list_watches(client: TestClient) -> None:
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.text = _MOCK_FORECAST_JSON
        mock_get.return_value.raise_for_status = lambda: None

        client.post(
            "/api/v1/weather/watches",
            json={"label": "广州", "latitude": 23.13, "longitude": 113.26},
            headers=auth_headers(),
        )
        client.post(
            "/api/v1/weather/watches",
            json={"label": "深圳", "latitude": 22.54, "longitude": 114.06},
            headers=auth_headers(),
        )

    resp = client.get("/api/v1/weather/watches", headers=auth_headers())
    assert resp.status_code == 200
    watches = resp.json()
    assert len(watches) >= 2
    labels = {w["label"] for w in watches}
    assert "广州" in labels
    assert "深圳" in labels


def test_get_watch(client: TestClient) -> None:
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.text = _MOCK_FORECAST_JSON
        mock_get.return_value.raise_for_status = lambda: None

        resp = client.post(
            "/api/v1/weather/watches",
            json={"label": "成都", "latitude": 30.57, "longitude": 104.07},
            headers=auth_headers(),
        )
        watch_id = resp.json()["id"]

    resp2 = client.get(f"/api/v1/weather/watches/{watch_id}", headers=auth_headers())
    assert resp2.status_code == 200
    assert resp2.json()["label"] == "成都"


def test_get_watch_not_found(client: TestClient) -> None:
    resp = client.get("/api/v1/weather/watches/99999", headers=auth_headers())
    assert resp.status_code == 404


def test_update_watch(client: TestClient) -> None:
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.text = _MOCK_FORECAST_JSON
        mock_get.return_value.raise_for_status = lambda: None

        resp = client.post(
            "/api/v1/weather/watches",
            json={"label": "杭州", "latitude": 30.25, "longitude": 120.16},
            headers=auth_headers(),
        )
        watch_id = resp.json()["id"]

    resp2 = client.put(
        f"/api/v1/weather/watches/{watch_id}",
        json={"label": "杭州(西湖)"},
        headers=auth_headers(),
    )
    assert resp2.status_code == 200
    assert resp2.json()["label"] == "杭州(西湖)"


def test_update_watch_not_found(client: TestClient) -> None:
    resp = client.put(
        "/api/v1/weather/watches/99999",
        json={"label": "不存在"},
        headers=auth_headers(),
    )
    assert resp.status_code == 404


def test_delete_watch(client: TestClient) -> None:
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.text = _MOCK_FORECAST_JSON
        mock_get.return_value.raise_for_status = lambda: None

        resp = client.post(
            "/api/v1/weather/watches",
            json={"label": "待删除", "latitude": 30.0, "longitude": 120.0},
            headers=auth_headers(),
        )
        watch_id = resp.json()["id"]

    resp2 = client.delete(f"/api/v1/weather/watches/{watch_id}", headers=auth_headers())
    assert resp2.status_code == 200
    assert resp2.json()["label"] == "待删除"

    resp3 = client.get(f"/api/v1/weather/watches/{watch_id}", headers=auth_headers())
    assert resp3.status_code == 404


def test_delete_watch_not_found(client: TestClient) -> None:
    resp = client.delete("/api/v1/weather/watches/99999", headers=auth_headers())
    assert resp.status_code == 404


def test_get_forecast_empty(client: TestClient) -> None:
    resp = client.get("/api/v1/weather/forecast", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_forecast_single(client: TestClient) -> None:
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.text = _MOCK_FORECAST_JSON
        mock_get.return_value.raise_for_status = lambda: None

        resp = client.post(
            "/api/v1/weather/watches",
            json={"label": "北京", "latitude": 39.906, "longitude": 116.391},
            headers=auth_headers(),
        )
        watch_id = resp.json()["id"]

    resp2 = client.get(f"/api/v1/weather/forecast/{watch_id}", headers=auth_headers())
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["watch_id"] == watch_id
    assert data["label"] == "北京"
    assert "days" in data
    assert "fetched_at" in data


def test_get_forecast_all(client: TestClient) -> None:
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.text = _MOCK_FORECAST_JSON
        mock_get.return_value.raise_for_status = lambda: None

        client.post(
            "/api/v1/weather/watches",
            json={"label": "北京", "latitude": 39.906, "longitude": 116.391},
            headers=auth_headers(),
        )
        client.post(
            "/api/v1/weather/watches",
            json={"label": "上海", "latitude": 31.23, "longitude": 121.47},
            headers=auth_headers(),
        )

    resp = client.get("/api/v1/weather/forecast", headers=auth_headers())
    assert resp.status_code == 200
    forecasts = resp.json()
    assert len(forecasts) >= 1


def test_get_forecast_not_found(client: TestClient) -> None:
    resp = client.get("/api/v1/weather/forecast/99999", headers=auth_headers())
    assert resp.status_code == 404


def test_get_forecast_refresh(client: TestClient) -> None:
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.text = _MOCK_FORECAST_JSON
        mock_get.return_value.raise_for_status = lambda: None

        resp = client.post(
            "/api/v1/weather/watches",
            json={"label": "测试", "latitude": 35.0, "longitude": 110.0},
            headers=auth_headers(),
        )
        watch_id = resp.json()["id"]

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.text = _MOCK_FORECAST_JSON
        mock_get.return_value.raise_for_status = lambda: None

        resp2 = client.get(
            f"/api/v1/weather/forecast/{watch_id}?refresh=true",
            headers=auth_headers(),
        )
        assert resp2.status_code == 200
        data = resp2.json()
        assert len(data["days"]) == 2
        assert data["days"][0]["date"] == "2026-07-17"


def test_invalid_latitude(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/weather/watches",
        json={"label": "测试", "latitude": 100.0, "longitude": 110.0},
        headers=auth_headers(),
    )
    assert resp.status_code == 422
