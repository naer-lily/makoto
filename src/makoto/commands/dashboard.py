"""数据总览命令。

提供今日数据概览：身体、饮食、运动汇总。
"""

from __future__ import annotations

from datetime import date
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

dashboard_app = typer.Typer(no_args_is_help=True)

BodyRow: TypeAlias = tuple[str, str]


@dashboard_app.command()
def today() -> None:
    """查看今日数据总览。"""
    console = get_console()
    profile = load_profile()
    assert profile is not None  # 已在 callback 中保证

    today_date = date.today()

    # ── 身体数据 ──
    body_store = JsonlStore(body_logs_path(), BodyLog)
    all_body = sorted(body_store.read_all(), key=lambda r: r.log_date, reverse=True)
    today_body = next((r for r in all_body if r.log_date == today_date), None)

    console.print(f"\n[bold underline]{today_date} 数据总览[/bold underline]\n")

    # 身体块
    console.print("[bold]身体[/bold]")
    if today_body is None:
        console.print("  [dim]本日未录入[/dim]")
    else:
        console.print(f"  体重: {today_body.weight_kg} kg    体脂率: {today_body.body_fat_pct}%")
        # 围度：本日有就用本日，否则回溯最新
        waist_val = today_body.waist_cm or (
            _latest_girth(all_body, "waist_cm", today_date)
        )
        arm_val = today_body.arm_cm or (
            _latest_girth(all_body, "arm_cm", today_date)
        )
        thigh_val = today_body.thigh_cm or (
            _latest_girth(all_body, "thigh_cm", today_date)
        )
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

    # ── 饮食 与 运动 ──
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
        food = food_store.find_one(
            (lambda fn: lambda f: f.name == fn)(d.food_name)
        )
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
        exercise_rows: list[list[str]] = []
        for r in today_exercises:
            exercise_rows.append([
                r.exercise_name,
                r.duration_desc,
                f"{r.calories_kcal:.0f} kcal",
            ])
        render_table(
            columns=["运动", "时长/数量", "消耗"],
            rows=exercise_rows,
            align=["left", "left", "right"],
            col_styles=["green", "", "yellow"],
        )
        console.print(f"  运动消耗:      {total_burned:.0f} kcal")
    else:
        console.print("  [dim]本日未录入[/dim]")

    # ── 净热量 ──
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


def _latest_girth(logs: list[BodyLog], field: str, before: date) -> float | None:
    """回溯查找指定字段最后一次非空记录（不含 before 当天）。

    Args:
        logs: 已按日期倒序排列的身体日志。
        field: BodyLog 的围度字段名。
        before: 排除日期。

    Returns:
        最近的非空值，若从未记录返回 None。
    """
    for r in logs:
        if r.log_date >= before:
            continue
        val = getattr(r, field, None)
        if isinstance(val, (int, float)):
            return val
    return None
