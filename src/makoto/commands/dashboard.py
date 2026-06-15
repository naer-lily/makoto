"""数据总览命令。

today: 今日数据概览（身体/饮食/运动/净热量）
report: 多日趋势报告（带七日均线的体重/体脂率/热量缺口）
"""

from __future__ import annotations

from datetime import date
from datetime import timedelta
from typing import TypeAlias

import typer

from makoto.models.records import BodyLog
from makoto.models.records import DietLog
from makoto.models.records import ExerciseLog
from makoto.models.records import Food
from makoto.utils.console import get_console
from makoto.utils.console import render_table
from makoto.utils.data_paths import body_logs_path
from makoto.utils.data_paths import diet_logs_path
from makoto.utils.data_paths import exercise_logs_path
from makoto.utils.data_paths import foods_path
from makoto.utils.jsonl_store import JsonlStore
from makoto.utils.profile_store import load as load_profile
from makoto.utils.timeseries import date_series
from makoto.utils.timeseries import linear_interpolate
from makoto.utils.timeseries import rolling_mean

dashboard_app = typer.Typer(no_args_is_help=True)

BodyRow: TypeAlias = tuple[str, str]


def _daily_diet_totals(
    dates: list[date],
    diet_store: JsonlStore[DietLog],
    food_store: JsonlStore[Food],
) -> dict[date, float]:
    """按日期汇总饮食摄入热量。

    Args:
        dates: 关注的日期列表。
        diet_store: 饮食数据存储。
        food_store: 食物数据存储。

    Returns:
        {日期: 总热量}，无饮食记录的日期为 0。
    """
    totals: dict[date, float] = dict.fromkeys(dates, 0.0)
    for record in diet_store.read_all():
        d = record.log_time.date()
        if d not in totals:
            continue
        food_name = record.food_name
        grams = record.grams
        food = food_store.find_one(lambda f, fn=food_name: f.name == fn)  # type: ignore[misc]
        if food is not None:
            totals[d] += food.nutrition_for(grams)["calories_kcal"]
    return totals


def _daily_exercise_totals(
    dates: list[date],
    exercise_store: JsonlStore[ExerciseLog],
) -> dict[date, float]:
    """按日期汇总运动消耗热量。

    Args:
        dates: 关注的日期列表。
        exercise_store: 运动数据存储。

    Returns:
        {日期: 总消耗}，无运动记录的日期为 0。
    """
    totals: dict[date, float] = dict.fromkeys(dates, 0.0)
    for record in exercise_store.read_all():
        d = record.log_time.date()
        if d in totals:
            totals[d] += record.calories_kcal
    return totals


@dashboard_app.command()
def today() -> None:
    """查看今日数据总览。"""
    console = get_console()
    profile = load_profile()
    assert profile is not None

    today_date = date.today()

    body_store = JsonlStore(body_logs_path(), BodyLog)
    all_body = sorted(body_store.read_all(), key=lambda r: r.log_date, reverse=True)
    today_body = next((r for r in all_body if r.log_date == today_date), None)

    console.print(f"\n[bold underline]{today_date} 数据总览[/bold underline]\n")

    # 身体块
    console.print("[bold]身体[/bold]")
    if today_body is None:
        console.print("  [dim]本日未录入[/dim]")
    else:
        console.print(
            f"  体重: {today_body.weight_kg} kg    体脂率: {today_body.body_fat_pct}%"
        )
        waist_val = today_body.waist_cm or _latest_girth(all_body, "waist_cm", today_date)
        arm_val = today_body.arm_cm or _latest_girth(all_body, "arm_cm", today_date)
        thigh_val = today_body.thigh_cm or _latest_girth(all_body, "thigh_cm", today_date)
        girths: list[str] = []
        if waist_val is not None:
            girths.append(f"腰围: {waist_val} cm")
        if arm_val is not None:
            girths.append(f"臂围: {arm_val} cm")
        if thigh_val is not None:
            girths.append(f"大腿围: {thigh_val} cm")
        if girths:
            console.print(f"  {'  '.join(girths)}")
        if today_body.note:
            console.print(f"  [dim]备注: {today_body.note}[/dim]")

    # 饮食 + 运动
    diet_store = JsonlStore(diet_logs_path(), DietLog)
    exercise_store = JsonlStore(exercise_logs_path(), ExerciseLog)
    food_store = JsonlStore(foods_path(), Food)

    today_diets = [r for r in diet_store.read_all() if r.log_time.date() == today_date]
    today_exercises = [
        r for r in exercise_store.read_all() if r.log_time.date() == today_date
    ]

    total_intake = 0.0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0
    for d in today_diets:
        food = food_store.find_one((lambda fn: lambda f: f.name == fn)(d.food_name))
        if food is not None:
            n = food.nutrition_for(d.grams)
            total_intake += n["calories_kcal"]
            total_protein += n["protein_g"]
            total_carbs += n["carbs_g"]
            total_fat += n["fat_g"]

    total_burned = sum(r.calories_kcal for r in today_exercises)
    net = profile.ree_kcal + total_burned - total_intake

    console.print(f"\n[bold]饮食[/bold] ({len(today_diets)} 条)")
    console.print(f"  REE 基础消耗:  {profile.ree_kcal:.0f} kcal/天")
    console.print(f"  今日摄入:      {total_intake:.0f} kcal")
    if total_intake > 0:
        console.print(
            f"  │ 蛋白质: {total_protein:.1f}g  "
            f"碳水: {total_carbs:.1f}g  "
            f"脂肪: {total_fat:.1f}g"
        )

    console.print(f"\n[bold]运动[/bold] ({len(today_exercises)} 条)")
    if today_exercises:
        exercise_rows: list[list[str]] = [
            [r.exercise_name, r.duration_desc, f"{r.calories_kcal:.0f} kcal"]
            for r in today_exercises
        ]
        render_table(
            columns=["运动", "时长/数量", "消耗"],
            rows=exercise_rows,
            align=["left", "left", "right"],
            col_styles=["green", "", "yellow"],
        )
        console.print(f"  运动消耗:      {total_burned:.0f} kcal")
    else:
        console.print("  [dim]本日未录入[/dim]")

    console.print("\n[bold underline]净热量[/bold underline]")
    console.print(f"  REE    {profile.ree_kcal:>8.0f} kcal")
    console.print(f"  运动   +{total_burned:>6.0f} kcal")
    console.print(f"  摄入   -{total_intake:>6.0f} kcal")
    console.print(f"  {'─' * 22}")
    if net > 0:
        label = "[green]缺口[/green]"
    elif net < 0:
        label = "[yellow]盈余[/yellow]"
    else:
        label = "平衡"
    console.print(f"  {label}  {abs(net):>8.0f} kcal")


@dashboard_app.command()
def report(
    range: str = typer.Option(
        "week", "--range", "-r", help="报告范围 (week | month)"
    ),
) -> None:
    """多日趋势报告：体重/体脂率七日均线 + 每日热量缺口。

    `*` 标记表示该值来自插值或前值继承，非原始录入。
    """
    console = get_console()
    profile = load_profile()
    assert profile is not None

    days = 30 if range == "month" else 7
    today_date = date.today()
    start_date = today_date - timedelta(days=days - 1)

    # 向前扩展 14 天缓冲区，确保插值有足够数据点
    buffer_start = start_date - timedelta(days=14)
    all_dates = date_series(buffer_start, today_date)

    body_store = JsonlStore(body_logs_path(), BodyLog)
    raw_weight: dict[date, float] = {}
    raw_body_fat: dict[date, float] = {}
    for r in body_store.read_all():
        if r.log_date >= buffer_start:
            raw_weight[r.log_date] = r.weight_kg
            raw_body_fat[r.log_date] = r.body_fat_pct

    weight_filled = linear_interpolate(raw_weight, all_dates)
    bf_filled = linear_interpolate(raw_body_fat, all_dates)

    # 纯值供 rolling_mean 用（全缓冲区）
    weight_cont: dict[date, float] = {d: v for d, (v, _) in weight_filled.items()}
    bf_cont: dict[date, float] = {d: v for d, (v, _) in bf_filled.items()}

    # 七日均线（全缓冲区，显示时仅取 display 部分）
    ma_weight_full = rolling_mean(weight_cont, window=7)
    ma_bf_full = rolling_mean(bf_cont, window=7)

    # 仅取显示区间
    display_dates = date_series(start_date, today_date)
    weight_original = {d: weight_filled[d][1] for d in display_dates if d in weight_filled}
    bf_original = {d: bf_filled[d][1] for d in display_dates if d in bf_filled}

    # 每日饮食/运动热量
    diet_store = JsonlStore(diet_logs_path(), DietLog)
    exercise_store = JsonlStore(exercise_logs_path(), ExerciseLog)
    food_store = JsonlStore(foods_path(), Food)
    daily_diet = _daily_diet_totals(display_dates, diet_store, food_store)
    daily_exercise = _daily_exercise_totals(display_dates, exercise_store)

    # 构建表格
    rows: list[list[str]] = []
    for d in display_dates:
        w = weight_cont.get(d, 0)
        bf = bf_cont.get(d, 0)
        mw = ma_weight_full.get(d, 0)
        mb = ma_bf_full.get(d, 0)

        balance = profile.ree_kcal + daily_exercise.get(d, 0.0) - daily_diet.get(d, 0.0)
        sign = "+" if balance > 0 else ""
        balance_str = f"{sign}{balance:.0f} kcal"

        w_str = f"{w:.1f} kg{'*' if not weight_original.get(d, False) else ''}"
        bf_str = f"{bf:.1f}%{'*' if not bf_original.get(d, False) else ''}"
        mw_str = f"{mw:.1f} kg"
        mb_str = f"{mb:.1f}%"

        rows.append([str(d), w_str, bf_str, mw_str, mb_str, balance_str])

    title = (
        f"{start_date} ~ {today_date} ({days} 天)"
        if range == "month"
        else f"{start_date} ~ {today_date}"
    )

    render_table(
        columns=["日期", "体重", "体脂率", "7日均重", "7日均脂", "热量缺口"],
        rows=rows,
        title=title,
        align=["left", "right", "right", "right", "right", "right"],
        col_styles=["cyan", "", "", "", "", "yellow"],
    )

    if any(not weight_original.get(d, True) for d in display_dates):
        console.print("[dim]* 标记表示该值来自插值或前值继承[/dim]")


def _latest_girth(logs: list[BodyLog], field: str, before: date) -> float | None:
    """回溯查找指定字段最后一次非空记录（不含 before 当天）。"""
    for r in logs:
        if r.log_date >= before:
            continue
        val = getattr(r, field, None)
        if isinstance(val, (int, float)):
            return val
    return None
