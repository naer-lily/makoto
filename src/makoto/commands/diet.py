"""饮食记录命令（CLI 客户端）。"""

from __future__ import annotations

from datetime import datetime

import typer

from makoto.client.api import ClientError
from makoto.client.api import get_client
from makoto.utils.console import get_console
from makoto.utils.console import render_table
from makoto.utils.tz import ensure_aware
from makoto.utils.tz import format_local

diet_app = typer.Typer(no_args_is_help=True)


@diet_app.command()
def log(
    log_time: datetime = typer.Option(
        ...,
        "--time",
        "-t",
        formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"],
        help="进餐时间（同分钟不可重复）",
    ),
    food_name: str = typer.Option(..., "--food", "-f", help="食物名称（须已注册）"),
    grams: float = typer.Option(..., "--grams", "-g", min=0, help="摄入克数"),
    note: str | None = typer.Option(None, "--note", "-n", help="备注"),
) -> None:
    """记录一次饮食（同分钟不可重复）。"""
    console = get_console()
    log_time_aware = ensure_aware(log_time)
    cli = get_client()
    try:
        result = cli.create_diet_log({
            "log_time": log_time_aware.isoformat(),
            "food_name": food_name,
            "grams": grams,
            "note": note,
        })
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(
        f"[green]已记录: {food_name} {grams}g | "
        f"{result['calories_kcal']:.0f} kcal  "
        f"P:{result['protein_g']:.1f}g  "
        f"C:{result['carbs_g']:.1f}g  "
        f"F:{result['fat_g']:.1f}g[/green]"
    )


@diet_app.command()
def delete(
    log_time: datetime = typer.Option(
        ...,
        "--time",
        "-t",
        formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"],
        help="要删除的进餐时间",
    ),
) -> None:
    """删除指定时间的饮食记录。"""
    console = get_console()
    log_time_aware = ensure_aware(log_time)
    time_str = log_time_aware.isoformat()
    cli = get_client()
    try:
        logs = cli.list_diet_logs(limit=9999)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    target = None
    for r in logs:
        # 比较时间字符串前缀（精确到分钟）
        if str(r.get("log_time", "")).startswith(time_str[:16]):
            target = r
            break

    if target is None:
        console.print(f"[red]{format_local(log_time)} 无记录。[/red]")
        raise typer.Exit(1)

    try:
        cli.delete_diet_log(target["id"])
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e
    console.print(f"[green]已删除 {format_local(log_time)} 饮食记录。[/green]")


@diet_app.command(name="list")
def list_diet(
    limit: int = typer.Option(50, "--limit", "-n", help="最大显示条数"),
) -> None:
    """列出饮食记录（按时间倒序）。"""
    console = get_console()
    cli = get_client()
    try:
        logs = cli.list_diet_logs(limit)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    if not logs:
        console.print("[dim]暂无饮食记录。[/dim]")
        return

    total_cal = 0.0
    rows: list[list[str]] = []
    for r in logs:
        cal = r.get("calories_kcal", 0)
        p = r.get("protein_g", 0)
        c = r.get("carbs_g", 0)
        fv = r.get("fat_g", 0)
        total_cal += float(cal)
        rows.append([
            str(r.get("log_time", "")),
            str(r.get("food_name", "")),
            f"{r.get('grams', 0):.0f}",
            f"{cal:.0f} kcal",
            f"{p:.1f} g",
            f"{c:.1f} g",
            f"{fv:.1f} g",
            r.get("note") or "",
        ])

    render_table(
        columns=["时间", "食物", "克数", "热量", "蛋白质", "碳水", "脂肪", "备注"],
        rows=rows,
        title="饮食记录",
        align=["left", "left", "right", "right", "right", "right", "right", "left"],
        col_styles=["cyan", "green", "", "yellow", "", "", "", "dim"],
    )

    console.print(f"[bold]显示 {len(logs)} 条，合计 {total_cal:.0f} kcal[/bold]")
