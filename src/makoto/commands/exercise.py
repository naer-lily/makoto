"""运动记录命令。"""

from __future__ import annotations

from datetime import datetime

import typer
from rich.table import Table

from makoto.models.records import ExerciseLog
from makoto.utils.console import get_console
from makoto.utils.data_paths import exercise_logs_path
from makoto.utils.jsonl_store import JsonlStore
from makoto.utils.tz import format_local

exercise_app = typer.Typer(no_args_is_help=True)
store = JsonlStore(exercise_logs_path(), ExerciseLog)


@exercise_app.command()
def log(
    log_time: datetime = typer.Option(
        ...,
        "--time",
        "-t",
        formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"],
        help="运动时间",
    ),
    name: str = typer.Option(..., "--name", "-n", help="运动名称"),
    duration: str = typer.Option(..., "--duration", "-d", help="时长/组数/数量"),
    calories: float = typer.Option(
        ..., "--calories", "-c", min=0, help="消耗热量（千卡）"
    ),
    note: str | None = typer.Option(None, "--note", help="备注"),
) -> None:
    """记录一次运动。"""
    console = get_console()
    record = ExerciseLog(
        log_time=log_time,
        exercise_name=name,
        duration_desc=duration,
        calories_kcal=calories,
        note=note,
    )
    store.append(record)
    console.print(
        f"[green]已记录运动: {name} {duration} / {calories:.0f} kcal[/green]"
    )


@exercise_app.command(name="list")
def list_exercise(
    limit: int = typer.Option(50, "--limit", "-n", help="最大显示条数"),
) -> None:
    """列出运动记录（按时间倒序）。"""
    console = get_console()
    logs = store.read_all()
    logs.sort(key=lambda r: r.log_time, reverse=True)
    logs = logs[:limit]

    if not logs:
        console.print("[dim]暂无运动记录。[/dim]")
        return

    table = Table(title="运动记录")
    table.add_column("时间", style="cyan")
    table.add_column("运动", style="green")
    table.add_column("时长/数量")
    table.add_column("消耗热量", justify="right", style="yellow")
    table.add_column("备注", style="dim")

    total_cal = 0.0
    for r in logs:
        total_cal += r.calories_kcal
        table.add_row(
            format_local(r.log_time),
            r.exercise_name,
            r.duration_desc,
            f"{r.calories_kcal:.0f} kcal",
            r.note or "",
        )

    console.print(table)
    console.print(f"[bold]显示 {len(logs)} 条，合计 {total_cal:.0f} kcal[/bold]")
