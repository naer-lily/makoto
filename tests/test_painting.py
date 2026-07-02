"""测试 /api/v1/painting-logs 端点。"""

from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def test_list_painting_logs_empty(client: TestClient) -> None:
    resp = client.get("/api/v1/painting-logs", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_and_list_painting_log(client: TestClient) -> None:
    payload = {
        "log_time": "2026-07-03T14:30:00",
        "file_path": "D:/ART/test.kra",
        "file_id": "test.kra",
        "duration_seconds": 1800.0,
    }
    resp = client.post(
        "/api/v1/painting-logs", json=payload, headers=auth_headers()
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["file_id"] == "test.kra"
    assert data["duration_seconds"] == 1800.0
    assert data["id"] >= 1

    list_resp = client.get("/api/v1/painting-logs", headers=auth_headers())
    assert len(list_resp.json()) == 1


def test_create_multiple_same_day(client: TestClient) -> None:
    """同一天允许多条绘画会话记录。"""
    payload1 = {
        "log_time": "2026-07-03T10:00:00",
        "file_path": "D:/ART/a.kra",
        "file_id": "a.kra",
        "duration_seconds": 600.0,
    }
    payload2 = {
        "log_time": "2026-07-03T14:00:00",
        "file_path": "D:/ART/b.kra",
        "file_id": "b.kra",
        "duration_seconds": 900.0,
    }
    r1 = client.post(
        "/api/v1/painting-logs", json=payload1, headers=auth_headers()
    )
    assert r1.status_code == 201
    r2 = client.post(
        "/api/v1/painting-logs", json=payload2, headers=auth_headers()
    )
    assert r2.status_code == 201

    list_resp = client.get("/api/v1/painting-logs", headers=auth_headers())
    assert len(list_resp.json()) == 2


def test_delete_painting_log(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/painting-logs",
        json={
            "log_time": "2026-07-03T08:00:00",
            "file_path": "D:/ART/delete-me.kra",
            "file_id": "delete-me.kra",
            "duration_seconds": 1200.0,
        },
        headers=auth_headers(),
    )
    log_id = resp.json()["id"]
    del_resp = client.delete(
        f"/api/v1/painting-logs/{log_id}", headers=auth_headers()
    )
    assert del_resp.status_code == 200

    list_resp = client.get("/api/v1/painting-logs", headers=auth_headers())
    assert len(list_resp.json()) == 0


def test_delete_painting_log_not_found(client: TestClient) -> None:
    resp = client.delete(
        "/api/v1/painting-logs/99999", headers=auth_headers()
    )
    assert resp.status_code == 404


def test_delete_returns_full_record(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/painting-logs",
        json={
            "log_time": "2026-07-03T08:00:00",
            "file_path": "D:/ART/full.kra",
            "file_id": "full.kra",
            "duration_seconds": 600.0,
        },
        headers=auth_headers(),
    )
    log_id = resp.json()["id"]
    del_resp = client.delete(
        f"/api/v1/painting-logs/{log_id}", headers=auth_headers()
    )
    assert del_resp.status_code == 200
    body = del_resp.json()
    assert body["id"] == log_id
    assert body["file_id"] == "full.kra"
    assert body["duration_seconds"] == 600.0


def test_update_painting_log(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/painting-logs",
        json={
            "log_time": "2026-07-03T08:00:00",
            "file_path": "D:/ART/old.kra",
            "file_id": "old.kra",
            "duration_seconds": 300.0,
        },
        headers=auth_headers(),
    )
    log_id = resp.json()["id"]

    payload = {
        "log_time": "2026-07-03T09:00:00",
        "file_path": "D:/ART/new.kra",
        "file_id": "new.kra",
        "duration_seconds": 900.0,
        "note": "修改后",
    }
    put_resp = client.put(
        f"/api/v1/painting-logs/{log_id}",
        json=payload,
        headers=auth_headers(),
    )
    assert put_resp.status_code == 200
    data = put_resp.json()
    assert data["file_id"] == "new.kra"
    assert data["duration_seconds"] == 900.0
    assert data["note"] == "修改后"


def test_update_painting_log_not_found(client: TestClient) -> None:
    resp = client.put(
        "/api/v1/painting-logs/99999",
        json={
            "log_time": "2026-07-03T08:00:00",
            "file_path": "D:/ART/x.kra",
            "file_id": "x.kra",
            "duration_seconds": 100.0,
        },
        headers=auth_headers(),
    )
    assert resp.status_code == 404


def test_list_painting_logs_date_filter(client: TestClient) -> None:
    for day in ("2026-07-01", "2026-07-02", "2026-07-03"):
        client.post(
            "/api/v1/painting-logs",
            json={
                "log_time": f"{day}T08:00:00",
                "file_path": f"D:/ART/{day}.kra",
                "file_id": f"{day}.kra",
                "duration_seconds": 600.0,
            },
            headers=auth_headers(),
        )

    only_02 = client.get(
        "/api/v1/painting-logs?start=2026-07-02&end=2026-07-02",
        headers=auth_headers(),
    )
    assert len(only_02.json()) == 1
    assert only_02.json()[0]["log_time"].startswith("2026-07-02")

    closed = client.get(
        "/api/v1/painting-logs?start=2026-07-01&end=2026-07-02",
        headers=auth_headers(),
    )
    assert len(closed.json()) == 2

    none_match = client.get(
        "/api/v1/painting-logs?start=2026-08-01",
        headers=auth_headers(),
    )
    assert none_match.json() == []
