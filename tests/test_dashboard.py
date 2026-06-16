"""测试 /api/v1/dashboard 端点。"""

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


def _seed_body_logs(client: TestClient) -> None:
    """录入多天身体数据以便 report 有数据。"""
    for day, w, bf in [
        ("2026-06-01", 72.0, 20.0),
        ("2026-06-03", 71.5, 19.5),
        ("2026-06-05", 71.0, 19.0),
        ("2026-06-08", 70.5, 18.5),
        ("2026-06-12", 70.0, 18.0),
        ("2026-06-15", 69.5, 17.5),
    ]:
        client.post(
            "/api/v1/body-logs",
            json={
                "log_date": day,
                "weight_kg": w,
                "body_fat_pct": bf,
            },
            headers=auth_headers(),
        )


def _seed_food(client: TestClient) -> None:
    client.post(
        "/api/v1/foods",
        json={"name": "鸡胸肉", "calories_per_100g": 133, "protein_per_100g": 31},
        headers=auth_headers(),
    )


def test_today_without_profile(client: TestClient) -> None:
    resp = client.get("/api/v1/dashboard/today", headers=auth_headers())
    assert resp.status_code == 404


def test_today_no_data(client: TestClient) -> None:
    _setup_profile(client)
    resp = client.get("/api/v1/dashboard/today", headers=auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert data["body"] is None
    assert data["diets"] == []
    assert data["exercises"] == []
    assert data["ree_kcal"] > 0


def test_today_with_body_and_diet(client: TestClient) -> None:
    _setup_profile(client)
    _seed_food(client)

    today = __import__("datetime").date.today().isoformat()
    log_time = f"{today}T12:30:00"

    client.post(
        "/api/v1/body-logs",
        json={
            "log_date": today,
            "weight_kg": 69.5,
            "body_fat_pct": 17.5,
        },
        headers=auth_headers(),
    )
    client.post(
        "/api/v1/diet-logs",
        json={"log_time": log_time, "food_name": "鸡胸肉", "grams": 200},
        headers=auth_headers(),
    )

    resp = client.get("/api/v1/dashboard/today", headers=auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert data["body"]["weight_kg"] == 69.5
    assert len(data["diets"]) == 1
    assert data["diets"][0]["calories_kcal"] == 266.0
    assert data["total_intake_kcal"] == 266.0
    assert "net_kcal" in data


def test_report_without_profile(client: TestClient) -> None:
    resp = client.get("/api/v1/dashboard/report", headers=auth_headers())
    assert resp.status_code == 404


def test_report_default_range(client: TestClient) -> None:
    _setup_profile(client)
    _seed_body_logs(client)

    resp = client.get("/api/v1/dashboard/report", headers=auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert "rows" in data
    assert "summary" in data
    assert "target_weight_kg" in data
    assert data["target_weight_kg"] == 65.0

    rows = data["rows"]
    assert len(rows) > 0

    first_row = rows[0]
    assert "weight_kg" in first_row
    assert "ma_weight_kg" in first_row
    assert "ma_body_fat_pct" in first_row
    assert "ma_ffm_kg" in first_row
    assert "deficit_kcal" in first_row
    assert "is_interpolated" in first_row
    assert "weekly_loss_kg" in first_row

    # summary 检查
    summary = data["summary"]
    assert "weight_delta" in summary
    assert "total_deficit_kcal" in summary


def test_report_custom_date_range(client: TestClient) -> None:
    _setup_profile(client)
    _seed_body_logs(client)

    resp = client.get(
        "/api/v1/dashboard/report?start_date=2026-06-01&end_date=2026-06-08",
        headers=auth_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["start_date"] == "2026-06-01"
    assert data["end_date"] == "2026-06-08"
    assert data["days"] == 8

    rows = data["rows"]
    assert len(rows) == 8  # date_series 连续生成
    assert rows[0]["date"] == "2026-06-01"
    assert rows[-1]["date"] == "2026-06-08"


def test_report_interpolation(client: TestClient) -> None:
    """验证缺少日期的数据会被插值。"""
    _setup_profile(client)
    _seed_body_logs(client)

    resp = client.get(
        "/api/v1/dashboard/report?start_date=2026-06-01&end_date=2026-06-05",
        headers=auth_headers(),
    )
    assert resp.status_code == 200
    rows = resp.json()["rows"]
    # 6/1(实测), 6/2(插值), 6/3(实测), 6/4(插值), 6/5(实测)
    assert rows[0]["is_interpolated"] is False  # 6/1
    assert rows[1]["is_interpolated"] is True  # 6/2
    assert rows[2]["is_interpolated"] is False  # 6/3


def test_weekly_loss_computed(client: TestClient) -> None:
    _setup_profile(client)
    # 录入 15 天数据让 7 日均线能算出周减重
    for day_offset in range(15):
        day = f"2026-06-{day_offset + 1:02d}"
        w = 75.0 - day_offset * 0.1
        client.post(
            "/api/v1/body-logs",
            json={"log_date": day, "weight_kg": w, "body_fat_pct": 18.0},
            headers=auth_headers(),
        )

    resp = client.get(
        "/api/v1/dashboard/report?start_date=2026-06-08&end_date=2026-06-15",
        headers=auth_headers(),
    )
    assert resp.status_code == 200
    rows = resp.json()["rows"]
    # 第 8 天之后 weekly_loss_kg 不应为 None
    later_rows = rows[7:]  # 6/15 = 最后一天
    assert any(r["weekly_loss_kg"] is not None for r in later_rows)
