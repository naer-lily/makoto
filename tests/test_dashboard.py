"""测试 /api/v1/dashboard 端点（不再返回 BIA 体脂/FFM/EA）。"""

from datetime import timedelta

from fastapi.testclient import TestClient

from makoto.utils.tz import today_local
from tests.conftest import auth_headers

_BIA_ROW_FIELDS = (
    "body_fat_pct",
    "ffm_kg",
    "fat_kg",
    "ma_body_fat_pct",
    "ma_ffm_kg",
    "ma_fat_kg",
    "alpert_limit_kcal",
    "ea_kcal_per_kg_ffm",
)


def _setup_profile(client: TestClient) -> None:
    """画像不再要求体脂率。"""
    client.put(
        "/api/v1/profile",
        json={
            "name": "测试",
            "gender": "male",
            "age": 30,
            "height_cm": 175,
            "weight_kg": 70,
            "target_weight_kg": 65,
            "target_date": "2026-12-31",
            "activity_level": "moderate",
        },
        headers=auth_headers(),
    )


def _seed_body_logs(client: TestClient) -> None:
    """录入多天体重；故意带旧体脂字段，验证服务端会丢弃。"""
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


def _assert_no_bia_row(row: dict[str, object]) -> None:
    for field in _BIA_ROW_FIELDS:
        assert row[field] is None, f"{field} should be None, got {row[field]!r}"


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
    assert data["ffm_kg"] is None
    assert data["ea_kcal_per_kg_ffm"] is None
    assert data["ea_level"] is None
    assert data["body_fat_delta_day"] is None
    assert data["body_fat_delta_week"] is None


def test_today_with_weight_and_diet_has_no_bia(client: TestClient) -> None:
    _setup_profile(client)
    food_id = _seed_food(client)

    today = today_local().isoformat()
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
    assert data["body"]["body_fat_pct"] == 17.5
    assert len(data["diets"]) == 1
    assert data["diets"][0]["calories_kcal"] == 266.0
    assert data["diets"][0]["fiber_g"] == 3.0  # 1.5 * 2
    assert data["total_intake_kcal"] == 266.0
    assert data["total_fiber_g"] == 3.0
    assert "net_kcal" in data
    assert data["ffm_kg"] is None
    assert data["ea_kcal_per_kg_ffm"] is None
    assert data["ea_level"] is None
    assert data["body_fat_delta_day"] is None
    assert data["body_fat_delta_week"] is None


def test_report_without_profile(client: TestClient) -> None:
    resp = client.get("/api/v1/dashboard/report", headers=auth_headers())
    assert resp.status_code == 404


def test_report_default_range_preserves_weights_without_bia(client: TestClient) -> None:
    _setup_profile(client)
    _seed_body_logs(client)

    resp = client.get("/api/v1/dashboard/report", headers=auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert "rows" in data
    assert "summary" in data
    assert data["target_weight_kg"] == 65.0

    rows = data["rows"]
    assert len(rows) > 0

    expected_weights = {
        "2026-06-01": 72.0,
        "2026-06-03": 71.5,
        "2026-06-05": 71.0,
        "2026-06-08": 70.5,
        "2026-06-12": 70.0,
        "2026-06-15": 69.5,
    }
    for row in rows:
        _assert_no_bia_row(row)
        if row["date"] in expected_weights:
            assert row["weight_kg"] == expected_weights[row["date"]]
            assert row["is_interpolated"] is False

    summary = data["summary"]
    assert summary["weight_delta"] == -2.5
    assert summary["body_fat_delta"] is None
    assert summary["ffm_delta"] is None
    assert summary["ma_body_fat_delta"] is None
    assert summary["ma_ffm_delta"] is None
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


def test_report_skips_days_without_diet_logs(client: TestClient) -> None:
    """没有饮食记录的日子不计缺口、不计期望值，也不进总天数。"""
    _setup_profile(client)
    _seed_body_logs(client)
    food_id = _seed_food(client)

    client.post(
        "/api/v1/diet-logs",
        json={"log_time": "2026-06-02T12:30:00", "food_id": food_id, "grams": 100},
        headers=auth_headers(),
    )

    resp = client.get(
        "/api/v1/dashboard/report?start_date=2026-06-01&end_date=2026-06-04",
        headers=auth_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    rows = {row["date"]: row for row in data["rows"]}

    assert rows["2026-06-01"]["has_diet_data"] is False
    assert rows["2026-06-01"]["deficit_kcal"] == 0
    assert rows["2026-06-01"]["expected_deficit_kcal"] is None
    assert rows["2026-06-01"]["ea_kcal_per_kg_ffm"] is None

    assert rows["2026-06-02"]["has_diet_data"] is True
    assert rows["2026-06-02"]["deficit_kcal"] != 0

    assert rows["2026-06-03"]["has_diet_data"] is False
    assert rows["2026-06-03"]["deficit_kcal"] == 0

    summary = data["summary"]
    assert summary["recorded_days"] == 1
    assert summary["total_deficit_kcal"] == rows["2026-06-02"]["deficit_kcal"]


def test_report_interpolation(client: TestClient) -> None:
    """验证缺少日期的体重会被插值，且不产生 BIA 派生值。"""
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
    for row in rows:
        _assert_no_bia_row(row)


def test_weekly_loss_computed_from_weight(client: TestClient) -> None:
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


def test_today_body_fat_delta_is_none_even_with_yesterday_record(
    client: TestClient,
) -> None:
    """有历史体重记录时也只给体重差值，不产生体脂日变化。"""
    _setup_profile(client)
    today = today_local()
    yesterday = (today - timedelta(days=1)).isoformat()

    client.post(
        "/api/v1/body-logs",
        json={"log_date": yesterday, "weight_kg": 70.0, "body_fat_pct": 20.0},
        headers=auth_headers(),
    )
    client.post(
        "/api/v1/body-logs",
        json={"log_date": today.isoformat(), "weight_kg": 69.0, "body_fat_pct": 19.0},
        headers=auth_headers(),
    )

    data = client.get("/api/v1/dashboard/today", headers=auth_headers()).json()
    assert data["body"]["weight_kg"] == 69.0
    assert data["weight_delta_day"] == -1.0
    assert data["body_fat_delta_day"] is None
    assert data["body"]["body_fat_pct"] == 19.0
