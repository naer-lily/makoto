"""数据总览命令。

today: 今日数据概览（身体/饮食/运动/净热量）
report: 多日趋势报告（带七日均线的体重/体脂率/热量缺口）
"""

from __future__ import annotations

import json
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

    total_burned = sum(r.calories_kcal for r in today_exercises)

    console.print(f"\n[bold]饮食[/bold] ({len(today_diets)} 条)")
    console.print(f"  REE 基础消耗:  {profile.ree_kcal:.0f} kcal/天")

    diet_rows: list[list[str]] = []
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
            diet_rows.append([
                d.food_name,
                f"{d.grams:.0f}g",
                f"{n['calories_kcal']:.0f} kcal",
                f"{n['protein_g']:.1f}g",
                f"{n['carbs_g']:.1f}g",
                f"{n['fat_g']:.1f}g",
            ])

    if diet_rows:
        render_table(
            columns=["食物", "克数", "热量", "蛋白质", "碳水", "脂肪"],
            rows=diet_rows,
            align=["left", "right", "right", "right", "right", "right"],
            col_styles=["green", "", "yellow", "", "", ""],
        )
        console.print(
            f"  [bold]合计: {total_intake:.0f} kcal"
            f"  P:{total_protein:.1f}g  C:{total_carbs:.1f}g  F:{total_fat:.1f}g[/bold]"
        )
    else:
        console.print("  [dim]本日未录入[/dim]")

    net = profile.ree_kcal + total_burned - total_intake

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
    json_output: bool = typer.Option(
        False, "--json", help="以 JSON 格式输出原始数据"
    ),
) -> None:
    """多日趋势报告：体重/体脂率/FFM/七日均线 + 每日热量缺口。

    `*` 标记表示该值来自插值或前值继承，非原始录入。
    """
    console = get_console()
    profile = load_profile()
    assert profile is not None

    days = 30 if range == "month" else 7
    today_date = date.today()
    start_date = today_date - timedelta(days=days - 1)

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

    weight_cont = {d: v for d, (v, _) in weight_filled.items()}
    bf_cont = {d: v for d, (v, _) in bf_filled.items()}

    # FFM 序列
    ffm_cont: dict[date, float] = {
        d: round(w * (1 - bf_cont.get(d, 0) / 100), 1) for d, w in weight_cont.items()
    }

    # 七日均线
    ma_weight_full = rolling_mean(weight_cont, window=7)
    ma_bf_full = rolling_mean(bf_cont, window=7)
    ma_ffm_full = rolling_mean(ffm_cont, window=7)

    display_dates = date_series(start_date, today_date)
    weight_original = {d: weight_filled[d][1] for d in display_dates if d in weight_filled}

    diet_store = JsonlStore(diet_logs_path(), DietLog)
    exercise_store = JsonlStore(exercise_logs_path(), ExerciseLog)
    food_store = JsonlStore(foods_path(), Food)
    daily_diet = _daily_diet_totals(display_dates, diet_store, food_store)
    daily_exercise = _daily_exercise_totals(display_dates, exercise_store)

    weekly_deficit = profile.weekly_deficit_needed
    daily_expected = (weekly_deficit / 7) if weekly_deficit is not None else None

    # ── 构建数据 ──
    data_rows: list[dict[str, object]] = []
    total_balance = 0.0
    total_expected = 0.0

    for d in display_dates:
        w = weight_cont.get(d, 0)
        bf = bf_cont.get(d, 0)
        ffm = ffm_cont.get(d, 0)
        mw = ma_weight_full.get(d, 0)
        mb = ma_bf_full.get(d, 0)
        mf = ma_ffm_full.get(d, 0)

        balance = profile.ree_kcal + daily_exercise.get(d, 0.0) - daily_diet.get(d, 0.0)
        total_balance += balance

        exp = daily_expected if daily_expected is not None else 0
        total_expected += exp

        is_orig = weight_original.get(d, False)

        data_rows.append({
            "date": str(d),
            "weight_kg": round(w, 1),
            "body_fat_pct": round(bf, 1),
            "ffm_kg": round(ffm, 1),
            "ma_weight_kg": round(mw, 1),
            "ma_body_fat_pct": round(mb, 1),
            "ma_ffm_kg": round(mf, 1),
            "deficit_kcal": round(balance, 1),
            "expected_deficit_kcal": round(exp, 1) if daily_expected is not None else None,
            "is_interpolated": not is_orig,
        })

    # ── JSON 输出 ──
    if json_output:
        first_row: dict[str, object] = data_rows[0] if data_rows else {}
        last_row: dict[str, object] = data_rows[-1] if data_rows else {}
        f_w = float(first_row.get("weight_kg", 0))  # type: ignore[arg-type]
        l_w = float(last_row.get("weight_kg", 0))  # type: ignore[arg-type]
        f_bf = float(first_row.get("body_fat_pct", 0))  # type: ignore[arg-type]
        l_bf = float(last_row.get("body_fat_pct", 0))  # type: ignore[arg-type]
        f_ffm = float(first_row.get("ffm_kg", 0))  # type: ignore[arg-type]
        l_ffm = float(last_row.get("ffm_kg", 0))  # type: ignore[arg-type]
        f_mw = float(first_row.get("ma_weight_kg", 0))  # type: ignore[arg-type]
        l_mw = float(last_row.get("ma_weight_kg", 0))  # type: ignore[arg-type]
        f_mb = float(first_row.get("ma_body_fat_pct", 0))  # type: ignore[arg-type]
        l_mb = float(last_row.get("ma_body_fat_pct", 0))  # type: ignore[arg-type]
        f_mf = float(first_row.get("ma_ffm_kg", 0))  # type: ignore[arg-type]
        l_mf = float(last_row.get("ma_ffm_kg", 0))  # type: ignore[arg-type]

        summary = {
            "weight_delta": round(l_w - f_w, 1),
            "body_fat_delta": round(l_bf - f_bf, 1),
            "ffm_delta": round(l_ffm - f_ffm, 1),
            "ma_weight_delta": round(l_mw - f_mw, 1),
            "ma_body_fat_delta": round(l_mb - f_mb, 1),
            "ma_ffm_delta": round(l_mf - f_mf, 1),
            "total_deficit_kcal": round(total_balance, 1),
            "total_expected_kcal": round(total_expected, 1) if daily_expected is not None else None,
            "met_target": total_balance >= total_expected if daily_expected is not None else None,
        }
        output = {
            "range": range,
            "start_date": str(start_date),
            "end_date": str(today_date),
            "days": days,
            "rows": data_rows,
            "summary": summary,
        }
        console.print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    # ── 表格输出 ──
    rows: list[list[str]] = []
    first_w = 0.0
    last_w = 0.0
    first_bf = 0.0
    last_bf = 0.0
    first_ffm = 0.0
    last_ffm = 0.0
    first_mw = 0.0
    last_mw = 0.0
    first_mb = 0.0
    last_mb = 0.0
    first_mf = 0.0
    last_mf = 0.0

    for i, rd in enumerate(data_rows):
        d_str = str(rd["date"])
        w_val = float(rd["weight_kg"])  # type: ignore[arg-type]
        bf_val = float(rd["body_fat_pct"])  # type: ignore[arg-type]
        ffm_val = float(rd["ffm_kg"])  # type: ignore[arg-type]
        mw_val = float(rd["ma_weight_kg"])  # type: ignore[arg-type]
        mb_val = float(rd["ma_body_fat_pct"])  # type: ignore[arg-type]
        mf_val = float(rd["ma_ffm_kg"])  # type: ignore[arg-type]
        bal_val = float(rd["deficit_kcal"])  # type: ignore[arg-type]
        exp_val = rd["expected_deficit_kcal"]
        interp = bool(rd["is_interpolated"])

        sign = "+" if bal_val > 0 else ""
        bal_str = f"{sign}{bal_val:.0f} kcal"
        exp_str = f"{exp_val:.0f} kcal" if exp_val is not None else "-"

        w_str = f"{w_val:.1f} kg{'*' if interp else ''}"
        bf_str = f"{bf_val:.1f}%{'*' if interp else ''}"
        ffm_str = f"{ffm_val:.1f} kg{'*' if interp else ''}"
        mw_str = f"{mw_val:.1f} kg"
        mb_str = f"{mb_val:.1f}%"
        mf_str = f"{mf_val:.1f} kg"

        if i == 0:
            first_w, first_bf, first_ffm = w_val, bf_val, ffm_val
            first_mw, first_mb, first_mf = mw_val, mb_val, mf_val
        last_w, last_bf, last_ffm = w_val, bf_val, ffm_val
        last_mw, last_mb, last_mf = mw_val, mb_val, mf_val

        rows.append([d_str, w_str, bf_str, ffm_str, mw_str, mb_str, mf_str, bal_str, exp_str])

    # 总计行
    w_delta = last_w - first_w
    bf_delta = last_bf - first_bf
    ffm_delta = last_ffm - first_ffm
    mw_delta = last_mw - first_mw
    mb_delta = last_mb - first_mb
    mf_delta = last_mf - first_mf
    exp_total_str = f"{total_expected:.0f} kcal" if daily_expected is not None else "-"

    rows.append([
        f"[bold]总计 ({len(display_dates)}天)[/bold]",
        f"[bold]{w_delta:+.1f} kg[/bold]",
        f"[bold]{bf_delta:+.1f}%[/bold]",
        f"[bold]{ffm_delta:+.1f} kg[/bold]",
        f"[bold]{mw_delta:+.1f} kg[/bold]",
        f"[bold]{mb_delta:+.1f}%[/bold]",
        f"[bold]{mf_delta:+.1f} kg[/bold]",
        f"[bold]{total_balance:+.0f} kcal[/bold]",
        f"[bold]{exp_total_str}[/bold]",
    ])

    title_text = (
        f"{start_date} ~ {today_date} ({days} 天)"
        if range == "month"
        else f"{start_date} ~ {today_date}"
    )
    render_table(
        columns=[
            "日期", "体重", "体脂率", "FFM",
            "7日均重", "7日均脂", "7均FFM",
            "热量缺口", "日期望",
        ],
        rows=rows,
        title=title_text,
        align=["left"] + ["right"] * 8,
        col_styles=["cyan", "", "", "", "", "", "", "yellow", "dim"],
    )

    if any(not weight_original.get(d, True) for d in display_dates):
        console.print("[dim]* 标记表示该值来自插值或前值继承[/dim]")

    if daily_expected is not None and total_balance < total_expected:
        console.print(
            f"[red]实际缺口 {total_balance:.0f} < 期望 {total_expected:.0f} kcal，未达标[/red]"
        )
    elif daily_expected is not None:
        console.print(
            f"[green]实际缺口 {total_balance:.0f} >= 期望 {total_expected:.0f} kcal，达标[/green]"
        )


def _latest_girth(logs: list[BodyLog], field: str, before: date) -> float | None:
    """回溯查找指定字段最后一次非空记录（不含 before 当天）。"""
    for r in logs:
        if r.log_date >= before:
            continue
        val = getattr(r, field, None)
        if isinstance(val, (int, float)):
            return val
    return None
