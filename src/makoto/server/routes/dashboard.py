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
from makoto.server.db_models import PaintingLog
from makoto.server.db_models import Profile
from makoto.server.keep_client import FitnessRecord
from makoto.server.keep_client import Keep
from makoto.server.models import ActivityLevel
from makoto.server.models import CircumferenceLogResponse
from makoto.server.models import Gender
from makoto.server.models import ReportResponse
from makoto.server.models import ReportRow
from makoto.server.models import ReportSummary
from makoto.server.models import TodayBody
from makoto.server.models import TodayDietItem
from makoto.server.models import TodayExerciseItem
from makoto.server.models import TodayPainting
from makoto.server.models import TodayPaintingItem
from makoto.server.models import TodayResponse
from makoto.server.models import nutrition_for
from makoto.utils.timeseries import date_series
from makoto.utils.timeseries import linear_interpolate
from makoto.utils.timeseries import rolling_mean
from makoto.utils.timeseries import rolling_mean_available
from makoto.utils.tz import today_local

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


async def _compute_deficit(
    session: AsyncSession,
    start_iso: str,
    end_iso: str,
    daily_netee: float,
    start_date: date,
    end_date: date,
) -> float:
    """计算指定日期段（含两端）的累计热量缺口。

    缺口 = NETEE * 天数 + 运动消耗 - 饮食摄入
    """
    diet_total = 0.0
    diet_days: set[date] = set()
    diet_rows = (
        await session.execute(
            select(DietLog).where(
                func.date(col(DietLog.log_time)) >= start_iso,
                func.date(col(DietLog.log_time)) <= end_iso,
            )
        )
    ).scalars().all()
    for dr in diet_rows:
        diet_days.add(datetime.fromisoformat(dr.log_time).date())
        food = (
            await session.execute(select(Food).where(Food.id == dr.food_id))
        ).scalar_one_or_none()
        if food is not None:
            diet_total += nutrition_for(
                food.calories_per_100g, 0, 0, 0, 0, dr.grams
            )["calories_kcal"]

    # 没有饮食记录的日子不参与缺口：既不算 NETEE，也不算当天运动。
    if not diet_days:
        return 0.0

    ex_total = 0.0
    ex_rows = (
        await session.execute(
            select(ExerciseLog).where(
                func.date(col(ExerciseLog.log_time)) >= start_iso,
                func.date(col(ExerciseLog.log_time)) <= end_iso,
            )
        )
    ).scalars().all()
    for er in ex_rows:
        if datetime.fromisoformat(er.log_time).date() in diet_days:
            ex_total += er.calories_kcal

    days = len(diet_days)
    return round(daily_netee * days + ex_total - diet_total, 1)


async def _fetch_fitness(session: AsyncSession) -> list[FitnessRecord]:
    """获取 Keep 体能水平数据。token 为空或请求失败时返回空列表。"""
    row = (await session.execute(select(Profile).where(Profile.id == 1))).scalar_one_or_none()
    if row is None or not row.keep_token:
        return []
    try:
        async with Keep(token=row.keep_token) as k:
            records: list[FitnessRecord] = await k.get_fitness()
            return records
    except Exception:
        return []


def _fitness_latest(records: list[FitnessRecord]) -> tuple[int | None, int | None, int | None]:
    """从 fitness 列表中取最新一条的 ATL / CTL / TSB。"""
    if not records:
        return None, None, None
    latest = records[-1]
    return latest.atl, latest.ctl, latest.tsb


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
    netee = round(bmr * activity.multiplier, 1)
    days = (target_date - today_local()).days
    weekly = None
    if days > 0:
        weekly = round((weight - target) * 7700 / (max(days / 7, 1)), 1)
    return {
        "netee_kcal": netee,
        "weekly_deficit_needed": weekly,
        "weight_kg": weight,
        "height_cm": height,
        "age": age,
        "gender": gender,
        "activity_level": activity,
        "target_weight_kg": target,
        "target_date": target_date,
    }


@router.get(
    "/today",
    response_model=TodayResponse,
    summary="今日数据总览",
    description=(
        "返回今日的身体测量、饮食明细、运动记录及净热量"
        "（NETEE + 运动消耗 - 饮食摄入）汇总。"
    ),
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

    # BIA 体脂/FFM/EA 已按主人要求移除，不再由体重反推任何体成分数值。

    # 饮食
    diets: list[TodayDietItem] = []
    total_intake = 0.0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0
    total_fiber = 0.0
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
                food.fiber_per_100g,
                dr.grams,
            )
            total_intake += n["calories_kcal"]
            total_protein += n["protein_g"]
            total_carbs += n["carbs_g"]
            total_fat += n["fat_g"]
            total_fiber += n["fiber_g"]
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
                    fiber_g=n["fiber_g"],
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

    netee = float(profile["netee_kcal"])
    net = netee + total_burned - total_intake

    # BIA 体成分（体脂/FFM/EA）不再计算，相关字段固定返回 None。

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
            forearm=circ_row.forearm,
            note=circ_row.note or None,
            created_at=circ_row.created_at or "",
        )

    # 昨日与上周差值
    weight_delta_day: float | None = None
    weight_delta_week: float | None = None
    if body is not None:
        yesterday = (today_date - timedelta(days=1)).isoformat()
        week_ago = (today_date - timedelta(days=7)).isoformat()

        prev_day = (
            await session.execute(select(BodyLog).where(BodyLog.log_date == yesterday))
        ).scalar_one_or_none()
        if prev_day is not None and body.weight_kg is not None:
            weight_delta_day = round(body.weight_kg - prev_day.weight_kg, 1)

        prev_week = (
            await session.execute(select(BodyLog).where(BodyLog.log_date == week_ago))
        ).scalar_one_or_none()
        if prev_week is not None and body.weight_kg is not None:
            weight_delta_week = round(body.weight_kg - prev_week.weight_kg, 1)

    # 本周、本月热量缺口（不含今日）
    deficit_week: float | None = None
    deficit_month: float | None = None

    yesterday_date = today_date - timedelta(days=1)
    yesterday_date_iso = yesterday_date.isoformat()

    week_start = today_date - timedelta(days=today_date.weekday())  # 本周一
    if week_start < today_date:
        deficit_week = await _compute_deficit(
            session, week_start.isoformat(), yesterday_date_iso, netee, week_start, yesterday_date
        )

    month_start = today_date.replace(day=1)
    if month_start < today_date:
        deficit_month = await _compute_deficit(
            session, month_start.isoformat(), yesterday_date_iso, netee, month_start, yesterday_date
        )

    fitness = await _fetch_fitness(session)

    # 绘画
    paint_rows = (
        await session.execute(
            select(PaintingLog).where(func.date(col(PaintingLog.log_time)) == today_iso)
        )
    ).scalars().all()
    paint_sessions = [
        TodayPaintingItem(
            log_time=r.log_time,
            file_id=r.file_id,
            file_path=r.file_path,
            duration_seconds=r.duration_seconds,
        )
        for r in paint_rows
    ]
    paint_duration = sum(r.duration_seconds for r in paint_rows)

    # 计算连续打卡天数
    all_dates_stmt = (
        select(func.date(col(PaintingLog.log_time)))
        .distinct()
        .order_by(col(PaintingLog.log_time).desc())
    )
    all_dates_result = await session.execute(all_dates_stmt)
    paint_dates_set = {date.fromisoformat(row[0]) for row in all_dates_result.all()}

    current_streak = 0
    d = today_date
    while d in paint_dates_set:
        current_streak += 1
        d -= timedelta(days=1)

    longest_streak = 0
    current_run = 0
    prev_date: date | None = None
    for d_sorted in sorted(paint_dates_set):
        if prev_date is not None and (d_sorted - prev_date).days == 1:
            current_run += 1
        else:
            current_run = 1
        longest_streak = max(longest_streak, current_run)
        prev_date = d_sorted

    painting = TodayPainting(
        painted_today=len(paint_rows) > 0,
        duration_seconds=paint_duration,
        session_count=len(paint_rows),
        sessions=paint_sessions,
        current_streak=current_streak,
        longest_streak=longest_streak,
        total_days=len(paint_dates_set),
    )

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
        total_fiber_g=round(total_fiber, 1),
        netee_kcal=netee,
        net_kcal=round(net, 1),
        weight_delta_day=weight_delta_day,
        body_fat_delta_day=None,
        weight_delta_week=weight_delta_week,
        body_fat_delta_week=None,
        deficit_week_kcal=deficit_week,
        deficit_month_kcal=deficit_month,
        circumference=circumference,
        atl=_fitness_latest(fitness)[0],
        ctl=_fitness_latest(fitness)[1],
        tsb=_fitness_latest(fitness)[2],
        painting=painting,
        ffm_kg=None,
        ea_kcal_per_kg_ffm=None,
        ea_level=None,
    )


@router.get(
    "/report",
    response_model=ReportResponse,
    summary="多日趋势报告",
    description="返回体重的逐日数据及七日均线，每日热量缺口，周减重速率。"
    "不再计算或返回 BIA 体脂/FFM/EA。默认从首条记录到目标日期。"
    "支持 start_date/end_date 自定义范围。",
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

    # 身体数据（只保留体重，BIA 体脂/FFM 不再参与计算）
    raw_weight: dict[date, float] = {}
    body_rows = (await session.execute(select(BodyLog))).scalars().all()
    for r in body_rows:
        d_date = date.fromisoformat(r.log_date)
        if d_date >= buffer_start:
            raw_weight[d_date] = r.weight_kg

    weight_filled = linear_interpolate(raw_weight, all_dates)
    weight_cont = {d: v for d, (v, _) in weight_filled.items()}
    ma_weight_full = rolling_mean(weight_cont, window=7)

    display_dates = date_series(start_date, end_date_date)
    weight_original = {d: weight_filled[d][1] for d in display_dates if d in weight_filled}

    # 饮食汇总
    daily_diet: dict[date, float] = dict.fromkeys(display_dates, 0.0)
    diet_days: set[date] = set()
    diet_rows = (await session.execute(select(DietLog))).scalars().all()
    for dr in diet_rows:
        d_date = datetime.fromisoformat(dr.log_time).date()
        if d_date not in daily_diet:
            continue
        diet_days.add(d_date)
        food = (
            await session.execute(select(Food).where(Food.id == dr.food_id))
        ).scalar_one_or_none()
        if food is not None:
            daily_diet[d_date] += nutrition_for(
                food.calories_per_100g, 0, 0, 0, 0, dr.grams
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

    netee = float(profile["netee_kcal"])

    # Keep 体能数据 — 以 YYYY-MM-DD 为 key 构建查找表
    fitness_records = await _fetch_fitness(session)
    fitness_map: dict[str, FitnessRecord] = {
        f.date.replace(".", "-"): f for f in fitness_records
    }

    # 热量缺口：只有当天有饮食记录才计算；空白日不参与均值和总计。
    daily_balance: dict[date, float] = {}
    for d in display_dates:
        if d in diet_days:
            daily_balance[d] = netee + daily_exercise.get(d, 0.0) - daily_diet.get(d, 0.0)
    ma_deficit = rolling_mean_available(daily_balance, display_dates, window=7)

    data_rows: list[ReportRow] = []
    total_balance = 0.0
    total_expected = 0.0

    for d in display_dates:
        w = weight_cont.get(d, 0)
        mw = ma_weight_full.get(d, 0)
        prev_mw = ma_weight_full.get(d - timedelta(days=7))
        weekly_loss = round(prev_mw - mw, 2) if prev_mw is not None else None
        has_diet = d in diet_days
        balance = daily_balance.get(d, 0.0)
        if has_diet:
            total_balance += balance
        exp = daily_expected if daily_expected is not None else 0
        if has_diet:
            total_expected += exp
        is_orig = weight_original.get(d, False)
        md = ma_deficit.get(d)
        intake = round(daily_diet.get(d, 0.0), 1)
        tdee = round(netee + daily_exercise.get(d, 0.0), 1)
        exercise = round(daily_exercise.get(d, 0.0), 1)
        fr = fitness_map.get(str(d))
        data_rows.append(
            ReportRow(
                date=str(d),
                weight_kg=round(w, 1),
                body_fat_pct=None,
                ffm_kg=None,
                fat_kg=None,
                ma_weight_kg=round(mw, 1),
                ma_body_fat_pct=None,
                ma_ffm_kg=None,
                ma_fat_kg=None,
                deficit_kcal=round(balance, 1),
                expected_deficit_kcal=(
                    round(exp, 1)
                    if has_diet and daily_expected is not None
                    else None
                ),
                alpert_limit_kcal=None,
                is_interpolated=not is_orig,
                has_diet_data=has_diet,
                weekly_loss_kg=weekly_loss,
                ma_deficit_kcal=round(md, 1) if md is not None else None,
                intake_kcal=intake,
                tdee_kcal=tdee,
                exercise_kcal=exercise,
                ea_kcal_per_kg_ffm=None,
                atl=fr.atl if fr else None,
                ctl=fr.ctl if fr else None,
                tsb=fr.tsb if fr else None,
            )
        )

    first: ReportRow = data_rows[0] if data_rows else ReportRow(
        date="", weight_kg=0,
        ma_weight_kg=0,
        deficit_kcal=0, expected_deficit_kcal=None,
        is_interpolated=False, weekly_loss_kg=None, ma_deficit_kcal=None,
        intake_kcal=0, tdee_kcal=0,
    )
    last: ReportRow = data_rows[-1] if data_rows else first

    summary = ReportSummary(
        weight_delta=round(last.weight_kg - first.weight_kg, 1),
        body_fat_delta=None,
        ffm_delta=None,
        ma_weight_delta=round(last.ma_weight_kg - first.ma_weight_kg, 1),
        ma_body_fat_delta=None,
        ma_ffm_delta=None,
        total_deficit_kcal=round(total_balance, 1),
        total_expected_kcal=round(total_expected, 1) if daily_expected is not None else None,
        recorded_days=len(diet_days),
        met_target=(
            total_balance >= total_expected
            if daily_expected is not None and diet_days
            else None
        ),
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
