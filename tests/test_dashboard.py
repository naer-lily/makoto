"""测试 /api/v1/dashboard 端点。"""

from datetime import date
from datetime import timedelta

import pytest
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


def _seed_food(client: TestClient) -> int:
    resp = client.post(
        "/api/v1/foods",
        json={
            "name": "鸡胸肉",
            "calories_per_100g": 133,
            "protein_per_100g": 31,
            "fiber_per_100g": 1.5,
        },
        headers=auth_headers(),
    )
    return int(resp.json()["id"])


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
    assert data["netee_kcal"] > 0


def test_today_with_body_and_diet(client: TestClient) -> None:
    _setup_profile(client)
    food_id = _seed_food(client)

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
        json={"log_time": log_time, "food_id": food_id, "grams": 200},
        headers=auth_headers(),
    )

    resp = client.get("/api/v1/dashboard/today", headers=auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert data["body"]["weight_kg"] == 69.5
    assert len(data["diets"]) == 1
    assert data["diets"][0]["calories_kcal"] == 266.0
    assert data["diets"][0]["fiber_g"] == 3.0  # 1.5 * 2
    assert data["total_intake_kcal"] == 266.0
    assert data["total_fiber_g"] == 3.0
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
    assert "ma_fat_kg" in first_row
    assert "deficit_kcal" in first_row
    assert "alpert_limit_kcal" in first_row
    assert "is_interpolated" in first_row
    assert "weekly_loss_kg" in first_row

    # 验证 Alpert 安全上限 = 脂肪重 kg × 60 kcal/kg
    for row in rows:
        fat_kg = float(row["fat_kg"])
        expected_limit = round(fat_kg * 60, 1)
        assert float(row["alpert_limit_kcal"]) == expected_limit

    # 验证 fat_kg + ffm_kg ≈ weight_kg
    for row in rows:
        fat = float(row["fat_kg"])
        ffm = float(row["ffm_kg"])
        wt = float(row["weight_kg"])
        assert abs(fat + ffm - wt) < 0.2

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


def test_today_ea_with_body_log(client: TestClient) -> None:
    """今日有身体记录时，FFM 与 EA 用今日数据计算。"""
    _setup_profile(client)
    food_id = _seed_food(client)
    today = date.today().isoformat()

    client.post(
        "/api/v1/body-logs",
        json={"log_date": today, "weight_kg": 69.5, "body_fat_pct": 17.5},
        headers=auth_headers(),
    )
    client.post(
        "/api/v1/diet-logs",
        json={"log_time": f"{today}T12:00:00", "food_id": food_id, "grams": 200},
        headers=auth_headers(),
    )
    client.post(
        "/api/v1/exercise-logs",
        json={
            "log_time": f"{today}T18:00:00",
            "exercise_name": "跑步",
            "duration_desc": "30分钟",
            "calories_kcal": 100,
        },
        headers=auth_headers(),
    )

    resp = client.get("/api/v1/dashboard/today", headers=auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    # FFM = 69.5 × (1 − 17.5%) = 57.3
    assert data["ffm_kg"] == 57.3
    # EA = (266 − 100) / 57.3 = 2.9
    assert data["ea_kcal_per_kg_ffm"] == 2.9
    assert data["ea_level"] == "low"


def test_today_ea_fallback_recent_body(client: TestClient) -> None:
    """今日无身体记录时，FFM 回退到最近一条身体记录。"""
    _setup_profile(client)
    food_id = _seed_food(client)
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    client.post(
        "/api/v1/body-logs",
        json={"log_date": yesterday, "weight_kg": 70.0, "body_fat_pct": 20.0},
        headers=auth_headers(),
    )
    client.post(
        "/api/v1/diet-logs",
        json={"log_time": f"{today}T12:00:00", "food_id": food_id, "grams": 200},
        headers=auth_headers(),
    )

    resp = client.get("/api/v1/dashboard/today", headers=auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert data["body"] is None  # 今日无记录，body 字段仍为空
    assert data["ffm_kg"] == 56.0  # 70.0 × (1 − 20%) = 56.0
    assert data["ea_kcal_per_kg_ffm"] == 4.8  # 266 / 56.0
    assert data["ea_level"] == "low"


def test_today_ea_without_body_record(client: TestClient) -> None:
    """完全无身体记录时，EA 相关字段全部为 None。"""
    _setup_profile(client)
    resp = client.get("/api/v1/dashboard/today", headers=auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert data["ffm_kg"] is None
    assert data["ea_kcal_per_kg_ffm"] is None
    assert data["ea_level"] is None


@pytest.mark.parametrize(
    ("intake_kcal", "expected_ea", "expected_level"),
    [
        (1140, 19.9, "low"),  # <20 偏低
        (1150, 20.1, "moderate"),  # 20-30 适中
        (1710, 29.8, "moderate"),  # 20-30 适中
        (1730, 30.2, "good"),  # 30-40 良好
        (2280, 39.8, "good"),  # 30-40 良好
        (2300, 40.1, "optimal"),  # >=40 最佳
    ],
)
def test_today_ea_level_boundaries(
    client: TestClient,
    intake_kcal: int,
    expected_ea: float,
    expected_level: str,
) -> None:
    """验证 EA 分级阈值：<20 偏低 / 20-30 适中 / 30-40 良好 / >=40 最佳。"""
    _setup_profile(client)
    today = date.today().isoformat()
    client.post(
        "/api/v1/body-logs",
        json={"log_date": today, "weight_kg": 69.5, "body_fat_pct": 17.5},
        headers=auth_headers(),
    )
    resp = client.post(
        "/api/v1/foods",
        json={"name": "基准食物", "calories_per_100g": 100},
        headers=auth_headers(),
    )
    food_id = int(resp.json()["id"])
    client.post(
        "/api/v1/diet-logs",
        json={
            "log_time": f"{today}T12:00:00",
            "food_id": food_id,
            "grams": intake_kcal,
        },
        headers=auth_headers(),
    )

    data = client.get("/api/v1/dashboard/today", headers=auth_headers()).json()
    assert data["ffm_kg"] == 57.3
    assert data["ea_kcal_per_kg_ffm"] == expected_ea
    assert data["ea_level"] == expected_level


def test_report_ea_fields(client: TestClient) -> None:
    """report 每行包含 exercise_kcal 与 ea_kcal_per_kg_ffm，公式正确。"""
    _setup_profile(client)
    _seed_body_logs(client)
    food_id = _seed_food(client)
    client.post(
        "/api/v1/diet-logs",
        json={"log_time": "2026-06-03T12:00:00", "food_id": food_id, "grams": 100},
        headers=auth_headers(),
    )
    client.post(
        "/api/v1/exercise-logs",
        json={
            "log_time": "2026-06-03T18:00:00",
            "exercise_name": "跑步",
            "duration_desc": "30分钟",
            "calories_kcal": 50,
        },
        headers=auth_headers(),
    )

    resp = client.get(
        "/api/v1/dashboard/report?start_date=2026-06-01&end_date=2026-06-05",
        headers=auth_headers(),
    )
    assert resp.status_code == 200
    rows = resp.json()["rows"]
    for row in rows:
        assert "exercise_kcal" in row
        assert "ea_kcal_per_kg_ffm" in row

    # 6/3：摄入 133 kcal，运动 50 kcal，FFM(插值) = 71.5 × 0.805 = 57.56
    row_3 = rows[2]
    assert row_3["exercise_kcal"] == 50.0
    assert row_3["intake_kcal"] == 133.0
    assert row_3["ea_kcal_per_kg_ffm"] == 1.4  # (133 − 50) / 57.56 = 1.44

    # 6/1：无饮食无运动 → EA 为 0
    assert rows[0]["ea_kcal_per_kg_ffm"] == 0.0


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
