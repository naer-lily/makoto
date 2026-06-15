"""数据总览 API 路由。"""

from __future__ import annotations

from datetime import date
from datetime import datetime
from datetime import timedelta
from typing import Any

import aiosqlite
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from makoto.server.auth import verify_token
from makoto.server.database import get_db
from makoto.server.models import ActivityLevel
from makoto.server.models import Gender
from makoto.server.models import ReportResponse
from makoto.server.models import ReportRow
from makoto.server.models import ReportSummary
from makoto.server.models import TodayBody
from makoto.server.models import TodayDietItem
from makoto.server.models import TodayExerciseItem
from makoto.server.models import TodayResponse
from makoto.server.models import nutrition_for
from makoto.utils.timeseries import date_series
from makoto.utils.timeseries import linear_interpolate
from makoto.utils.timeseries import rolling_mean

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


def _bmr(weight: float, height: float, age: int, gender: Gender) -> float:
    base = 10 * weight + 6.25 * height - 5 * age
    return round(base + 5 if gender == Gender.MALE else base - 161, 1)


async def _get_profile_computed(db: aiosqlite.Connection) -> dict[str, Any]:
    cursor = await db.execute("SELECT * FROM profile WHERE id = 1")
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="用户画像未设置")
    d = dict(row)
    gender = Gender(str(d["gender"]))
    activity = ActivityLevel(str(d["activity_level"]))
    weight = float(d["weight_kg"])
    height = float(d["height_cm"])
    age = int(d["age"])
    target = float(d["target_weight_kg"])
    target_date = date.fromisoformat(str(d["target_date"]))
    bmr = _bmr(weight, height, age, gender)
    ree = round(bmr * activity.multiplier, 1)
    days = (target_date - date.today()).days
    weekly = None
    if days > 0:
        weekly = round((weight - target) * 7700 / (max(days / 7, 1)), 1)
    return {
        "ree_kcal": ree,
        "weekly_deficit_needed": weekly,
        "weight_kg": weight,
        "height_cm": height,
        "age": age,
        "body_fat_pct": float(d["body_fat_pct"]),
        "gender": gender,
        "activity_level": activity,
        "target_weight_kg": target,
        "target_date": target_date,
    }


@router.get(
    "/today",
    response_model=TodayResponse,
    summary="今日数据总览",
    description="返回今日的身体测量、饮食明细、运动记录及净热量（REE + 运动消耗 - 饮食摄入）汇总。",
)
async def today_dashboard(
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> TodayResponse:
    profile = await _get_profile_computed(db)
    today_date = date.today()

    # 身体
    body: TodayBody | None = None
    cursor = await db.execute(
        "SELECT * FROM body_log WHERE log_date = ?", (today_date.isoformat(),)
    )
    body_row = await cursor.fetchone()
    if body_row is not None:
        d = dict(body_row)
        waist = float(d["waist_cm"]) if d["waist_cm"] is not None else None
        arm = float(d["arm_cm"]) if d["arm_cm"] is not None else None
        thigh = float(d["thigh_cm"]) if d["thigh_cm"] is not None else None
        if waist is None or arm is None or thigh is None:
            cursor2 = await db.execute(
                "SELECT waist_cm, arm_cm, thigh_cm FROM body_log WHERE log_date < ? "
                "AND (waist_cm IS NOT NULL OR arm_cm IS NOT NULL OR thigh_cm IS NOT NULL) "
                "ORDER BY log_date DESC LIMIT 1",
                (today_date.isoformat(),),
            )
            prev = await cursor2.fetchone()
            if prev is not None:
                if waist is None and prev["waist_cm"] is not None:
                    waist = float(prev["waist_cm"])
                if arm is None and prev["arm_cm"] is not None:
                    arm = float(prev["arm_cm"])
                if thigh is None and prev["thigh_cm"] is not None:
                    thigh = float(prev["thigh_cm"])
        body = TodayBody(
            weight_kg=float(d["weight_kg"]),
            body_fat_pct=float(d["body_fat_pct"]),
            waist_cm=waist,
            arm_cm=arm,
            thigh_cm=thigh,
            note=str(d["note"]) if d["note"] else None,
        )

    # 饮食
    diets: list[TodayDietItem] = []
    total_intake = 0.0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0
    cursor = await db.execute(
        "SELECT * FROM diet_log WHERE date(log_time) = ?", (today_date.isoformat(),)
    )
    diet_rows = await cursor.fetchall()
    for dr in diet_rows:
        dd = dict(dr)
        food_name = str(dd["food_name"])
        grams_val = float(dd["grams"])
        cf = await db.execute(
            "SELECT calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g "
            "FROM food WHERE name = ?",
            (food_name,),
        )
        frow = await cf.fetchone()
        if frow is not None:
            n = nutrition_for(
                float(frow["calories_per_100g"]),
                float(frow["protein_per_100g"]),
                float(frow["carbs_per_100g"]),
                float(frow["fat_per_100g"]),
                grams_val,
            )
            total_intake += n["calories_kcal"]
            total_protein += n["protein_g"]
            total_carbs += n["carbs_g"]
            total_fat += n["fat_g"]
            diets.append(
                TodayDietItem(
                    food_name=food_name,
                    grams=grams_val,
                    calories_kcal=n["calories_kcal"],
                    protein_g=n["protein_g"],
                    carbs_g=n["carbs_g"],
                    fat_g=n["fat_g"],
                )
            )

    # 运动
    exercises: list[TodayExerciseItem] = []
    total_burned = 0.0
    cursor = await db.execute(
        "SELECT * FROM exercise_log WHERE date(log_time) = ?", (today_date.isoformat(),)
    )
    ex_rows = await cursor.fetchall()
    for er in ex_rows:
        ed = dict(er)
        cal = float(ed["calories_kcal"])
        total_burned += cal
        exercises.append(
            TodayExerciseItem(
                exercise_name=str(ed["exercise_name"]),
                duration_desc=str(ed["duration_desc"]),
                calories_kcal=cal,
            )
        )

    ree = float(profile["ree_kcal"])
    net = ree + total_burned - total_intake

    return TodayResponse(
        date=today_date,
        body=body,
        diets=diets,
        exercises=exercises,
        total_intake_kcal=round(total_intake, 1),
        total_burned_kcal=round(total_burned, 1),
        total_protein_g=round(total_protein, 1),
        total_carbs_g=round(total_carbs, 1),
        total_fat_g=round(total_fat, 1),
        ree_kcal=ree,
        net_kcal=round(net, 1),
    )


@router.get(
    "/report",
    response_model=ReportResponse,
    summary="多日趋势报告",
    description="返回体重/体脂率/FFM 的逐日数据及七日均线，以及每日热量缺口和预期缺口汇总。",
)
async def dashboard_report(
    range: str = Query("week", alias="range"),
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> ReportResponse:
    profile = await _get_profile_computed(db)
    days = 30 if range == "month" else 7
    today_date = date.today()
    start_date = today_date - timedelta(days=days - 1)
    buffer_start = start_date - timedelta(days=14)
    all_dates = date_series(buffer_start, today_date)

    # 身体数据
    raw_weight: dict[date, float] = {}
    raw_body_fat: dict[date, float] = {}
    cursor = await db.execute("SELECT log_date, weight_kg, body_fat_pct FROM body_log")
    body_rows = await cursor.fetchall()
    for r in body_rows:
        bd = dict(r)
        d_date = date.fromisoformat(str(bd["log_date"]))
        if d_date >= buffer_start:
            raw_weight[d_date] = float(bd["weight_kg"])
            raw_body_fat[d_date] = float(bd["body_fat_pct"])

    weight_filled = linear_interpolate(raw_weight, all_dates)
    bf_filled = linear_interpolate(raw_body_fat, all_dates)

    weight_cont = {d: v for d, (v, _) in weight_filled.items()}
    bf_cont = {d: v for d, (v, _) in bf_filled.items()}

    ffm_cont: dict[date, float] = {
        d: round(w * (1 - bf_cont.get(d, 0) / 100), 1) for d, w in weight_cont.items()
    }

    ma_weight_full = rolling_mean(weight_cont, window=7)
    ma_bf_full = rolling_mean(bf_cont, window=7)
    ma_ffm_full = rolling_mean(ffm_cont, window=7)

    display_dates = date_series(start_date, today_date)
    weight_original = {d: weight_filled[d][1] for d in display_dates if d in weight_filled}

    # 饮食汇总
    daily_diet: dict[date, float] = dict.fromkeys(display_dates, 0.0)
    cursor = await db.execute("SELECT log_time, food_name, grams FROM diet_log")
    diet_rows = await cursor.fetchall()
    for dr in diet_rows:
        dd = dict(dr)
        log_time_str = str(dd["log_time"])
        d_date = datetime.fromisoformat(log_time_str).date()
        if d_date not in daily_diet:
            continue
        food_name = str(dd["food_name"])
        grams_val = float(dd["grams"])
        cf = await db.execute(
            "SELECT calories_per_100g FROM food WHERE name = ?", (food_name,)
        )
        frow = await cf.fetchone()
        if frow is not None:
            daily_diet[d_date] += nutrition_for(
                float(frow["calories_per_100g"]), 0, 0, 0, grams_val
            )["calories_kcal"]

    # 运动汇总
    daily_exercise: dict[date, float] = dict.fromkeys(display_dates, 0.0)
    cursor = await db.execute("SELECT log_time, calories_kcal FROM exercise_log")
    ex_rows = await cursor.fetchall()
    for er in ex_rows:
        ed = dict(er)
        d_date = datetime.fromisoformat(str(ed["log_time"])).date()
        if d_date in daily_exercise:
            daily_exercise[d_date] += float(ed["calories_kcal"])

    weekly_deficit = profile.get("weekly_deficit_needed")
    daily_expected = float(weekly_deficit) / 7 if weekly_deficit is not None else None

    ree = float(profile["ree_kcal"])

    data_rows: list[ReportRow] = []
    total_balance = 0.0
    total_expected = 0.0

    for d in display_dates:
        w = weight_cont.get(d, 0)
        bf = bf_cont.get(d, 0)
        ffm = ffm_cont.get(d, 0)
        mw = ma_weight_full.get(d, 0)
        mb = ma_bf_full.get(d, 0)
        mf = ma_ffm_full.get(d, 0)
        balance = ree + daily_exercise.get(d, 0.0) - daily_diet.get(d, 0.0)
        total_balance += balance
        exp = daily_expected if daily_expected is not None else 0
        total_expected += exp
        is_orig = weight_original.get(d, False)
        data_rows.append(
            ReportRow(
                date=str(d),
                weight_kg=round(w, 1),
                body_fat_pct=round(bf, 1),
                ffm_kg=round(ffm, 1),
                ma_weight_kg=round(mw, 1),
                ma_body_fat_pct=round(mb, 1),
                ma_ffm_kg=round(mf, 1),
                deficit_kcal=round(balance, 1),
                expected_deficit_kcal=round(exp, 1) if daily_expected is not None else None,
                is_interpolated=not is_orig,
            )
        )

    first = data_rows[0] if data_rows else ReportRow(
        date="", weight_kg=0, body_fat_pct=0, ffm_kg=0,
        ma_weight_kg=0, ma_body_fat_pct=0, ma_ffm_kg=0,
        deficit_kcal=0, expected_deficit_kcal=None, is_interpolated=False,
    )
    last = data_rows[-1] if data_rows else first

    summary = ReportSummary(
        weight_delta=round(last.weight_kg - first.weight_kg, 1),
        body_fat_delta=round(last.body_fat_pct - first.body_fat_pct, 1),
        ffm_delta=round(last.ffm_kg - first.ffm_kg, 1),
        ma_weight_delta=round(last.ma_weight_kg - first.ma_weight_kg, 1),
        ma_body_fat_delta=round(last.ma_body_fat_pct - first.ma_body_fat_pct, 1),
        ma_ffm_delta=round(last.ma_ffm_kg - first.ma_ffm_kg, 1),
        total_deficit_kcal=round(total_balance, 1),
        total_expected_kcal=round(total_expected, 1) if daily_expected is not None else None,
        met_target=total_balance >= total_expected if daily_expected is not None else None,
    )

    return ReportResponse(
        range=range,
        start_date=str(start_date),
        end_date=str(today_date),
        days=days,
        rows=data_rows,
        summary=summary,
    )
