"""测试 /api/v1/exercise-logs 端点。"""

from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def test_list_exercise_logs_empty(client: TestClient) -> None:
    resp = client.get("/api/v1/exercise-logs", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_and_list_exercise_log(client: TestClient) -> None:
    payload = {
        "log_time": "2026-06-15T08:00:00",
        "exercise_name": "跑步",
        "duration_desc": "5公里",
        "calories_kcal": 320.0,
    }
    resp = client.post(
        "/api/v1/exercise-logs", json=payload, headers=auth_headers()
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["exercise_name"] == "跑步"
    assert data["calories_kcal"] == 320.0

    list_resp = client.get("/api/v1/exercise-logs", headers=auth_headers())
    assert len(list_resp.json()) == 1


def test_create_exercise_log_duplicate_time(client: TestClient) -> None:
    payload = {
        "log_time": "2026-06-15T09:00:00",
        "exercise_name": "游泳",
        "duration_desc": "30分钟",
        "calories_kcal": 200.0,
    }
    resp1 = client.post(
        "/api/v1/exercise-logs", json=payload, headers=auth_headers()
    )
    assert resp1.status_code == 201

    resp2 = client.post(
        "/api/v1/exercise-logs", json=payload, headers=auth_headers()
    )
    assert resp2.status_code == 409


def test_delete_exercise_log(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/exercise-logs",
        json={
            "log_time": "2026-06-14T07:00:00",
            "exercise_name": "瑜伽",
            "duration_desc": "1小时",
            "calories_kcal": 150.0,
        },
        headers=auth_headers(),
    )
    log_id = resp.json()["id"]
    resp2 = client.delete(
        f"/api/v1/exercise-logs/{log_id}", headers=auth_headers()
    )
    assert resp2.status_code == 200

    resp3 = client.get("/api/v1/exercise-logs", headers=auth_headers())
    assert len(resp3.json()) == 0


def test_update_exercise_log(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/exercise-logs",
        json={
            "log_time": "2026-06-15T08:00:00",
            "exercise_name": "跑步",
            "duration_desc": "3公里",
            "calories_kcal": 200.0,
        },
        headers=auth_headers(),
    )
    log_id = resp.json()["id"]

    payload = {
        "log_time": "2026-06-15T09:00:00",
        "exercise_name": "慢跑",
        "duration_desc": "5公里",
        "calories_kcal": 350.0,
    }
    resp2 = client.put(
        f"/api/v1/exercise-logs/{log_id}", json=payload, headers=auth_headers()
    )
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["exercise_name"] == "慢跑"
    assert data["calories_kcal"] == 350.0


def test_update_exercise_log_not_found(client: TestClient) -> None:
    resp = client.put(
        "/api/v1/exercise-logs/99999",
        json={
            "log_time": "2026-06-15T08:00:00",
            "exercise_name": "跑步",
            "duration_desc": "5公里",
            "calories_kcal": 300.0,
        },
        headers=auth_headers(),
    )
    assert resp.status_code == 404


def test_update_exercise_log_duplicate_time(client: TestClient) -> None:
    _r1 = client.post(
        "/api/v1/exercise-logs",
        json={
            "log_time": "2026-06-15T10:00:00",
            "exercise_name": "游泳",
            "duration_desc": "30分钟",
            "calories_kcal": 200.0,
        },
        headers=auth_headers(),
    )
    r2 = client.post(
        "/api/v1/exercise-logs",
        json={
            "log_time": "2026-06-15T11:00:00",
            "exercise_name": "骑行",
            "duration_desc": "1小时",
            "calories_kcal": 400.0,
        },
        headers=auth_headers(),
    )

    resp = client.put(
        f"/api/v1/exercise-logs/{r2.json()['id']}",
        json={
            "log_time": "2026-06-15T10:00:00",
            "exercise_name": "骑行",
            "duration_desc": "1小时",
            "calories_kcal": 400.0,
        },
        headers=auth_headers(),
    )
    assert resp.status_code == 409


def test_delete_exercise_log_returns_full_record(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/exercise-logs",
        json={
            "log_time": "2026-06-14T07:00:00",
            "exercise_name": "瑜伽",
            "duration_desc": "1小时",
            "calories_kcal": 150.0,
        },
        headers=auth_headers(),
    )
    log_id = resp.json()["id"]
    del_resp = client.delete(
        f"/api/v1/exercise-logs/{log_id}", headers=auth_headers()
    )
    assert del_resp.status_code == 200
    body = del_resp.json()
    assert body["id"] == log_id
    assert body["exercise_name"] == "瑜伽"
    assert body["calories_kcal"] == 150.0


def test_list_exercise_logs_date_filter(client: TestClient) -> None:
    for day in ("2026-06-18", "2026-06-19", "2026-06-20"):
        client.post(
            "/api/v1/exercise-logs",
            json={
                "log_time": f"{day}T07:00:00",
                "exercise_name": "跑步",
                "duration_desc": "5公里",
                "calories_kcal": 300.0,
            },
            headers=auth_headers(),
        )

    only_19 = client.get(
        "/api/v1/exercise-logs?start=2026-06-19&end=2026-06-19",
        headers=auth_headers(),
    )
    assert len(only_19.json()) == 1
    assert only_19.json()[0]["log_time"].startswith("2026-06-19")

    closed = client.get(
        "/api/v1/exercise-logs?start=2026-06-18&end=2026-06-19",
        headers=auth_headers(),
    )
    assert len(closed.json()) == 2

    none_match = client.get(
        "/api/v1/exercise-logs?start=2026-07-01", headers=auth_headers()
    )
    assert none_match.json() == []
