"""运动记录命令。

同一分钟仅允许一条记录（需相差至少 1 分钟）。
"""

from __future__ import annotations

from datetime import datetime

import typer

from makoto.models.records import ExerciseLog
from makoto.utils.console import get_console
from makoto.utils.console import render_table
from makoto.utils.data_paths import exercise_logs_path
from makoto.utils.jsonl_store import JsonlStore
from makoto.utils.tz import ensure_aware
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
        help="运动时间（同分钟不可重复）",
    ),
    name: str = typer.Option(..., "--name", "-n", help="运动名称"),
    duration: str = typer.Option(..., "--duration", "-d", help="时长/组数/数量"),
    calories: float = typer.Option(
        ..., "--calories", "-c", min=0, help="消耗热量（千卡）"
    ),
    note: str | None = typer.Option(None, "--note", help="备注"),
) -> None:
    """记录一次运动（同分钟不可重复）。"""
    console = get_console()
    log_time_aware = ensure_aware(log_time)
    if store.find_one(lambda r: r.log_time == log_time_aware) is not None:
        console.print(
            f"[red]{format_local(log_time)} 已有记录，请错开至少 1 分钟。[/red]"
        )
        raise typer.Exit(1)

    record = ExerciseLog(
        log_time=log_time_aware,
        exercise_name=name,
        duration_desc=duration,
        calories_kcal=calories,
        note=note,
    )
    store.append(record)
    console.print(
        f"[green]已记录运动: {name} {duration} / {calories:.0f} kcal[/green]"
    )


@exercise_app.command()
def delete(
    log_time: datetime = typer.Option(
        ...,
        "--time",
        "-t",
        formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"],
        help="要删除的运动时间",
    ),
) -> None:
    """删除指定时间的运动记录。"""
    console = get_console()
    log_time_aware = ensure_aware(log_time)
    deleted = store.delete_many(lambda r: r.log_time == log_time_aware)
    if deleted == 0:
        console.print(f"[red]{format_local(log_time)} 无记录。[/red]")
        raise typer.Exit(1)

    console.print(f"[green]已删除 {format_local(log_time)} 运动记录。[/green]")


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

    total_cal = 0.0
    rows: list[list[str]] = []
    for r in logs:
        total_cal += r.calories_kcal
        rows.append([
            format_local(r.log_time),
            r.exercise_name,
            r.duration_desc,
            f"{r.calories_kcal:.0f} kcal",
            r.note or "",
        ])

    render_table(
        columns=["时间", "运动", "时长/数量", "消耗热量", "备注"],
        rows=rows,
        title="运动记录",
        align=["left", "left", "left", "right", "left"],
        col_styles=["cyan", "green", "", "yellow", "dim"],
    )

    console.print(f"[bold]显示 {len(logs)} 条，合计 {total_cal:.0f} kcal[/bold]")
