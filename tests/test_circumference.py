"""测试 /api/v1/circumference-logs 端点。"""

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from makoto.commands.circumference import _circumference_detail_fields
from makoto.main import app
from makoto.utils.tz import today_local
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
        "forearm": 28.0,
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
    assert data["forearm"] == 28.0

    list_resp = client.get("/api/v1/circumference-logs", headers=auth_headers())
    assert len(list_resp.json()) == 1


def test_create_circumference_partial(client: TestClient) -> None:
    """部分字段为 None 也可创建。"""
    payload = {
        "log_date": "2026-06-16",
        "waist_cm": 79.5,
        "arm_cm": None,
        "thigh_cm": None,
        "forearm": None,
    }
    resp = client.post(
        "/api/v1/circumference-logs", json=payload, headers=auth_headers()
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["waist_cm"] == 79.5
    assert data["arm_cm"] is None
    assert data["thigh_cm"] is None
    assert data["forearm"] is None


def test_create_circumference_forearm_negative(client: TestClient) -> None:
    """小臂围必须 >= 0。"""
    payload = {"log_date": "2026-06-17", "forearm": -0.1}
    resp = client.post(
        "/api/v1/circumference-logs", json=payload, headers=auth_headers()
    )
    assert resp.status_code == 422


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
        json={
            "log_date": "2026-06-13",
            "waist_cm": 82.0,
            "arm_cm": 33.0,
            "forearm": 28.5,
        },
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
    assert body["forearm"] == 28.5


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


def test_today_dashboard_includes_forearm(client: TestClient) -> None:
    """今日仪表盘返回的围度数据包含小臂围。"""
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
            "target_date": "2099-12-31",
            "activity_level": "moderate",
        },
        headers=auth_headers(),
    )
    day = today_local().isoformat()
    resp = client.post(
        "/api/v1/circumference-logs",
        json={
            "log_date": day,
            "waist_cm": 86.5,
            "arm_cm": 34.1,
            "thigh_cm": 58.5,
            "forearm": 28.0,
        },
        headers=auth_headers(),
    )
    assert resp.status_code == 201

    dashboard_resp = client.get("/api/v1/dashboard/today", headers=auth_headers())
    assert dashboard_resp.status_code == 200
    circumference = dashboard_resp.json()["circumference"]
    assert circumference is not None
    assert circumference["forearm"] == 28.0


def test_cli_circumference_log_help_includes_forearm() -> None:
    """CLI 记录命令暴露 --forearm 选项。"""
    result = CliRunner().invoke(app, ["circumference", "log", "--help"])
    assert result.exit_code == 0
    assert "--forearm" in result.stdout


def test_circumference_detail_fields_include_forearm() -> None:
    """围度详情字段包含小臂围。"""
    fields = dict(_circumference_detail_fields({"forearm": 28.0}))
    assert fields["小臂围"] == "28.0 cm"
