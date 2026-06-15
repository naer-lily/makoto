"""饮食记录命令。"""

from __future__ import annotations

from datetime import datetime

import typer

from makoto.models.records import DietLog
from makoto.models.records import Food
from makoto.utils.console import get_console
from makoto.utils.console import render_table
from makoto.utils.data_paths import diet_logs_path
from makoto.utils.data_paths import foods_path
from makoto.utils.jsonl_store import JsonlStore
from makoto.utils.tz import format_local

diet_app = typer.Typer(no_args_is_help=True)
diet_store = JsonlStore(diet_logs_path(), DietLog)
food_store = JsonlStore(foods_path(), Food)


@diet_app.command()
def log(
    log_time: datetime = typer.Option(
        ...,
        "--time",
        "-t",
        formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"],
        help="进餐时间",
    ),
    food_name: str = typer.Option(..., "--food", "-f", help="食物名称（须已注册）"),
    grams: float = typer.Option(..., "--grams", "-g", min=0, help="摄入克数"),
    note: str | None = typer.Option(None, "--note", "-n", help="备注"),
) -> None:
    """记录一次饮食。"""
    console = get_console()
    if food_store.find_one(lambda f: f.name == food_name) is None:
        console.print(f"[red]食物 '{food_name}' 未注册，请先 makoto food add。[/red]")
        raise typer.Exit(1)

    record = DietLog(log_time=log_time, food_name=food_name, grams=grams, note=note)
    diet_store.append(record)

    food = food_store.find_one(lambda f: f.name == food_name)
    assert food is not None
    nutrition = food.nutrition_for(grams)
    console.print(
        f"[green]已记录: {food_name} {grams}g | "
        f"{nutrition['calories_kcal']:.0f} kcal  "
        f"P:{nutrition['protein_g']:.1f}g  "
        f"C:{nutrition['carbs_g']:.1f}g  "
        f"F:{nutrition['fat_g']:.1f}g[/green]"
    )


@diet_app.command(name="list")
def list_diet(
    limit: int = typer.Option(50, "--limit", "-n", help="最大显示条数"),
) -> None:
    """列出饮食记录（按时间倒序）。"""
    console = get_console()
    logs = diet_store.read_all()
    logs.sort(key=lambda r: r.log_time, reverse=True)
    logs = logs[:limit]

    if not logs:
        console.print("[dim]暂无饮食记录。[/dim]")
        return

    total_cal = 0.0
    rows: list[list[str]] = []
    for r in logs:
        food = food_store.find_one(
            (lambda fn: lambda f: f.name == fn)(r.food_name)
        )
        if food is None:
            cal, p, c, fv = 0.0, 0.0, 0.0, 0.0
        else:
            n = food.nutrition_for(r.grams)
            cal, p, c, fv = n["calories_kcal"], n["protein_g"], n["carbs_g"], n["fat_g"]

        total_cal += cal
        rows.append([
            format_local(r.log_time),
            r.food_name,
            f"{r.grams:.0f}",
            f"{cal:.0f} kcal",
            f"{p:.1f} g",
            f"{c:.1f} g",
            f"{fv:.1f} g",
            r.note or "",
        ])

    render_table(
        columns=["时间", "食物", "克数", "热量", "蛋白质", "碳水", "脂肪", "备注"],
        rows=rows,
        title="饮食记录",
        align=["left", "left", "right", "right", "right", "right", "right", "left"],
        col_styles=["cyan", "green", "", "yellow", "", "", "", "dim"],
    )

    console.print(f"[bold]显示 {len(logs)} 条，合计 {total_cal:.0f} kcal[/bold]")
