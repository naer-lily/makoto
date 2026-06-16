"""运动记录命令（CLI 客户端）。"""

from __future__ import annotations

from datetime import datetime

import typer

from makoto.client.api import ClientError
from makoto.client.api import get_client
from makoto.utils.console import get_console
from makoto.utils.console import render_table
from makoto.utils.tz import ensure_aware
from makoto.utils.tz import format_local
from makoto.utils.tz import to_store_str

exercise_app = typer.Typer(no_args_is_help=True)


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
    cli = get_client()
    try:
        cli.create_exercise_log({
            "log_time": to_store_str(log_time_aware),
            "exercise_name": name,
            "duration_desc": duration,
            "calories_kcal": calories,
            "note": note,
        })
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

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
    time_str = to_store_str(log_time_aware)
    cli = get_client()
    try:
        logs = cli.list_exercise_logs(limit=9999)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    target = None
    for r in logs:
        if str(r.get("log_time", "")).startswith(time_str[:16]):
            target = r
            break

    if target is None:
        console.print(f"[red]{format_local(log_time)} 无记录。[/red]")
        raise typer.Exit(1)

    try:
        cli.delete_exercise_log(target["id"])
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e
    console.print(f"[green]已删除 {format_local(log_time)} 运动记录。[/green]")


@exercise_app.command(name="list")
def list_exercise(
    limit: int = typer.Option(50, "--limit", "-n", help="最大显示条数"),
) -> None:
    """列出运动记录（按时间倒序）。"""
    console = get_console()
    cli = get_client()
    try:
        logs = cli.list_exercise_logs(limit)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    if not logs:
        console.print("[dim]暂无运动记录。[/dim]")
        return

    total_cal = 0.0
    rows: list[list[str]] = []
    for r in logs:
        cal = float(r.get("calories_kcal", 0))
        total_cal += cal
        rows.append([
            str(r.get("log_time", "")),
            str(r.get("exercise_name", "")),
            str(r.get("duration_desc", "")),
            f"{cal:.0f} kcal",
            r.get("note") or "",
        ])

    render_table(
        columns=["时间", "运动", "时长/数量", "消耗热量", "备注"],
        rows=rows,
        title="运动记录",
        align=["left", "left", "left", "right", "left"],
        col_styles=["cyan", "green", "", "yellow", "dim"],
    )

    console.print(f"[bold]显示 {len(logs)} 条，合计 {total_cal:.0f} kcal[/bold]")
