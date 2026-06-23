"""数据总览 API 路由。"""

from __future__ import annotations

from datetime import date
from datetime import datetime
from datetime import timedelta
from typing import Any

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col
from sqlmodel import select

from makoto.server.auth import verify_token
from makoto.server.database import get_session
from makoto.server.db_models import BodyLog
from makoto.server.db_models import CircumferenceLog
from makoto.server.db_models import DietLog
from makoto.server.db_models import ExerciseLog
from makoto.server.db_models import Food
from makoto.server.db_models import Profile
from makoto.server.models import ActivityLevel
from makoto.server.models import CircumferenceLogResponse
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
from makoto.utils.tz import today_local

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


def _bmr(weight: float, height: float, age: int, gender: Gender) -> float:
    base = 10 * weight + 6.25 * height - 5 * age
    return round(base + 5 if gender == Gender.MALE else base - 161, 1)


async def _get_profile_computed(session: AsyncSession) -> dict[str, Any]:
    row = (
        await session.execute(select(Profile).where(Profile.id == 1))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="用户画像未设置")
    gender = Gender(row.gender)
    activity = ActivityLevel(row.activity_level)
    weight = row.weight_kg
    height = row.height_cm
    age = row.age
    target = row.target_weight_kg
    target_date = date.fromisoformat(row.target_date)
    bmr = _bmr(weight, height, age, gender)
    ree = round(bmr * activity.multiplier, 1)
    days = (target_date - today_local()).days
    weekly = None
    if days > 0:
        weekly = round((weight - target) * 7700 / (max(days / 7, 1)), 1)
    return {
        "ree_kcal": ree,
        "weekly_deficit_needed": weekly,
        "weight_kg": weight,
        "height_cm": height,
        "age": age,
        "body_fat_pct": row.body_fat_pct,
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
    session: AsyncSession = Depends(get_session),
) -> TodayResponse:
    profile = await _get_profile_computed(session)
    today_date = today_local()
    today_iso = today_date.isoformat()

    # 身体
    body: TodayBody | None = None
    body_row = (
        await session.execute(select(BodyLog).where(BodyLog.log_date == today_iso))
    ).scalar_one_or_none()
    if body_row is not None:
        body = TodayBody(
            weight_kg=body_row.weight_kg,
            body_fat_pct=body_row.body_fat_pct,
            note=body_row.note or None,
        )

    # 饮食
    diets: list[TodayDietItem] = []
    total_intake = 0.0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0
    diet_rows = (
        await session.execute(
            select(DietLog).where(func.date(col(DietLog.log_time)) == today_iso)
        )
    ).scalars().all()
    for dr in diet_rows:
        food = (
            await session.execute(select(Food).where(Food.id == dr.food_id))
        ).scalar_one_or_none()
        if food is not None:
            n = nutrition_for(
                food.calories_per_100g,
                food.protein_per_100g,
                food.carbs_per_100g,
                food.fat_per_100g,
                dr.grams,
            )
            total_intake += n["calories_kcal"]
            total_protein += n["protein_g"]
            total_carbs += n["carbs_g"]
            total_fat += n["fat_g"]
            diets.append(
                TodayDietItem(
                    log_time=dr.log_time,
                    food_id=dr.food_id,
                    food_name=food.name,
                    grams=dr.grams,
                    calories_kcal=n["calories_kcal"],
                    protein_g=n["protein_g"],
                    carbs_g=n["carbs_g"],
                    fat_g=n["fat_g"],
                )
            )

    # 运动
    exercises: list[TodayExerciseItem] = []
    total_burned = 0.0
    ex_rows = (
        await session.execute(
            select(ExerciseLog).where(func.date(col(ExerciseLog.log_time)) == today_iso)
        )
    ).scalars().all()
    for er in ex_rows:
        total_burned += er.calories_kcal
        exercises.append(
            TodayExerciseItem(
                log_time=er.log_time,
                exercise_name=er.exercise_name,
                duration_desc=er.duration_desc,
                calories_kcal=er.calories_kcal,
            )
        )

    ree = float(profile["ree_kcal"])
    net = ree + total_burned - total_intake

    # 当日围度
    circumference: CircumferenceLogResponse | None = None
    circ_row = (
        await session.execute(
            select(CircumferenceLog).where(CircumferenceLog.log_date == today_iso)
        )
    ).scalar_one_or_none()
    if circ_row is not None:
        assert circ_row.id is not None
        circumference = CircumferenceLogResponse(
            id=circ_row.id,
            log_date=today_date,
            waist_cm=circ_row.waist_cm,
            arm_cm=circ_row.arm_cm,
            thigh_cm=circ_row.thigh_cm,
            note=circ_row.note or None,
            created_at=circ_row.created_at or "",
        )

    # 昨日与上周差值
    weight_delta_day: float | None = None
    body_fat_delta_day: float | None = None
    weight_delta_week: float | None = None
    body_fat_delta_week: float | None = None
    if body is not None:
        yesterday = (today_date - timedelta(days=1)).isoformat()
        week_ago = (today_date - timedelta(days=7)).isoformat()

        prev_day = (
            await session.execute(select(BodyLog).where(BodyLog.log_date == yesterday))
        ).scalar_one_or_none()
        if prev_day is not None and body.weight_kg is not None:
            weight_delta_day = round(body.weight_kg - prev_day.weight_kg, 1)
        if prev_day is not None and body.body_fat_pct is not None:
            body_fat_delta_day = round(body.body_fat_pct - prev_day.body_fat_pct, 1)

        prev_week = (
            await session.execute(select(BodyLog).where(BodyLog.log_date == week_ago))
        ).scalar_one_or_none()
        if prev_week is not None and body.weight_kg is not None:
            weight_delta_week = round(body.weight_kg - prev_week.weight_kg, 1)
        if prev_week is not None and body.body_fat_pct is not None:
            body_fat_delta_week = round(body.body_fat_pct - prev_week.body_fat_pct, 1)

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
        weight_delta_day=weight_delta_day,
        body_fat_delta_day=body_fat_delta_day,
        weight_delta_week=weight_delta_week,
        body_fat_delta_week=body_fat_delta_week,
        circumference=circumference,
    )


@router.get(
    "/report",
    response_model=ReportResponse,
    summary="多日趋势报告",
    description="返回体重/体脂率/FFM 的逐日数据及七日均线，每日热量缺口，周减重速率。"
    "默认从首条记录到目标日期。支持 start_date/end_date 自定义范围。",
)
async def dashboard_report(
    start_date_str: str | None = Query(None, alias="start_date"),
    end_date_str: str | None = Query(None, alias="end_date"),
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> ReportResponse:
    profile = await _get_profile_computed(session)
    target_date = profile.get("target_date")
    target_weight = profile.get("target_weight_kg")
    today_date = today_local()

    start_date = date.fromisoformat(start_date_str) if start_date_str else None
    user_end = date.fromisoformat(end_date_str) if end_date_str else None

    if start_date is None:
        min_date = (
            await session.execute(select(func.min(col(BodyLog.log_date))))
        ).scalar_one_or_none()
        start_date = date.fromisoformat(min_date) if min_date else today_date

    if user_end is not None:
        end_date_date = user_end
    else:
        max_date = (
            await session.execute(select(func.max(col(BodyLog.log_date))))
        ).scalar_one_or_none()
        end_date_date = date.fromisoformat(max_date) if max_date else today_date

    buffer_start = start_date - timedelta(days=14)
    all_dates = date_series(buffer_start, end_date_date)

    # 身体数据
    raw_weight: dict[date, float] = {}
    raw_body_fat: dict[date, float] = {}
    body_rows = (await session.execute(select(BodyLog))).scalars().all()
    for r in body_rows:
        d_date = date.fromisoformat(r.log_date)
        if d_date >= buffer_start:
            raw_weight[d_date] = r.weight_kg
            raw_body_fat[d_date] = r.body_fat_pct

    weight_filled = linear_interpolate(raw_weight, all_dates)
    bf_filled = linear_interpolate(raw_body_fat, all_dates)

    weight_cont = {d: v for d, (v, _) in weight_filled.items()}
    bf_cont = {d: v for d, (v, _) in bf_filled.items()}

    ffm_cont: dict[date, float] = {
        d: round(w * (1 - bf_cont.get(d, 0) / 100), 1) for d, w in weight_cont.items()
    }
    fat_cont: dict[date, float] = {
        d: round(w * bf_cont.get(d, 0) / 100, 1) for d, w in weight_cont.items()
    }

    ma_weight_full = rolling_mean(weight_cont, window=7)
    ma_bf_full = rolling_mean(bf_cont, window=7)
    ma_ffm_full = rolling_mean(ffm_cont, window=7)
    ma_fat_full = rolling_mean(fat_cont, window=7)

    display_dates = date_series(start_date, end_date_date)
    weight_original = {d: weight_filled[d][1] for d in display_dates if d in weight_filled}

    # 饮食汇总
    daily_diet: dict[date, float] = dict.fromkeys(display_dates, 0.0)
    diet_rows = (await session.execute(select(DietLog))).scalars().all()
    for dr in diet_rows:
        d_date = datetime.fromisoformat(dr.log_time).date()
        if d_date not in daily_diet:
            continue
        food = (
            await session.execute(select(Food).where(Food.id == dr.food_id))
        ).scalar_one_or_none()
        if food is not None:
            daily_diet[d_date] += nutrition_for(
                food.calories_per_100g, 0, 0, 0, dr.grams
            )["calories_kcal"]

    # 运动汇总
    daily_exercise: dict[date, float] = dict.fromkeys(display_dates, 0.0)
    ex_rows = (await session.execute(select(ExerciseLog))).scalars().all()
    for er in ex_rows:
        d_date = datetime.fromisoformat(er.log_time).date()
        if d_date in daily_exercise:
            daily_exercise[d_date] += er.calories_kcal

    weekly_deficit = profile.get("weekly_deficit_needed")
    daily_expected = float(weekly_deficit) / 7 if weekly_deficit is not None else None

    ree = float(profile["ree_kcal"])

    # 热量缺口 7 日均线
    daily_balance: dict[date, float] = {}
    for d in display_dates:
        daily_balance[d] = ree + daily_exercise.get(d, 0.0) - daily_diet.get(d, 0.0)
    ma_deficit = rolling_mean(daily_balance, window=7)

    data_rows: list[ReportRow] = []
    total_balance = 0.0
    total_expected = 0.0

    for d in display_dates:
        w = weight_cont.get(d, 0)
        bf = bf_cont.get(d, 0)
        ffm = ffm_cont.get(d, 0)
        fat = fat_cont.get(d, 0)
        mw = ma_weight_full.get(d, 0)
        mb = ma_bf_full.get(d, 0)
        mf = ma_ffm_full.get(d, 0)
        mfa = ma_fat_full.get(d, 0)
        prev_mw = ma_weight_full.get(d - timedelta(days=7))
        weekly_loss = round(prev_mw - mw, 2) if prev_mw is not None else None
        balance = daily_balance[d]
        total_balance += balance
        exp = daily_expected if daily_expected is not None else 0
        total_expected += exp
        is_orig = weight_original.get(d, False)
        md = ma_deficit.get(d)
        data_rows.append(
            ReportRow(
                date=str(d),
                weight_kg=round(w, 1),
                body_fat_pct=round(bf, 1),
                ffm_kg=round(ffm, 1),
                fat_kg=round(fat, 1),
                ma_weight_kg=round(mw, 1),
                ma_body_fat_pct=round(mb, 1),
                ma_ffm_kg=round(mf, 1),
                ma_fat_kg=round(mfa, 1),
                deficit_kcal=round(balance, 1),
                expected_deficit_kcal=round(exp, 1) if daily_expected is not None else None,
                is_interpolated=not is_orig,
                weekly_loss_kg=weekly_loss,
                ma_deficit_kcal=round(md, 1) if md is not None else None,
            )
        )

    first: ReportRow = data_rows[0] if data_rows else ReportRow(
        date="", weight_kg=0, body_fat_pct=0, ffm_kg=0, fat_kg=0,
        ma_weight_kg=0, ma_body_fat_pct=0, ma_ffm_kg=0, ma_fat_kg=0,
        deficit_kcal=0, expected_deficit_kcal=None, is_interpolated=False,
        weekly_loss_kg=None, ma_deficit_kcal=None,
    )
    last: ReportRow = data_rows[-1] if data_rows else first

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
        start_date=str(start_date),
        end_date=str(end_date_date),
        days=(end_date_date - start_date).days + 1,
        target_weight_kg=float(target_weight) if target_weight is not None else None,
        target_date=str(target_date) if target_date is not None else None,
        rows=data_rows,
        summary=summary,
    )
