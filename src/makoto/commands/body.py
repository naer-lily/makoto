"""身体测量记录命令（CLI 客户端）。"""

from __future__ import annotations

from datetime import date

import typer

from makoto.client.api import ClientError
from makoto.client.api import get_client
from makoto.utils.console import get_console
from makoto.utils.console import render_table

body_app = typer.Typer(no_args_is_help=True)


@body_app.command()
def log(
    log_date: str = typer.Option(
        ..., "--date", "-d", help="测量日期 (YYYY-MM-DD)，每天仅一条"
    ),
    weight: float = typer.Option(..., "--weight", "-w", min=0, help="体重（公斤）"),
    body_fat: float = typer.Option(
        ..., "--body-fat", "-b", min=0, max=60, help="体脂率（%）"
    ),
    waist: float | None = typer.Option(None, "--waist", min=0, help="腰围（厘米）"),
    arm: float | None = typer.Option(None, "--arm", min=0, help="臂围（厘米）"),
    thigh: float | None = typer.Option(None, "--thigh", min=0, help="大腿围（厘米）"),
    note: str | None = typer.Option(None, "--note", "-n", help="备注"),
) -> None:
    """记录晨起身体测量数据（每天仅一条）。"""
    console = get_console()
    try:
        date.fromisoformat(log_date)
    except ValueError as e:
        console.print(f"[red]日期格式无效 '{log_date}'，请使用 YYYY-MM-DD。[/red]")
        raise typer.Exit(1) from e

    cli = get_client()
    try:
        cli.create_body_log({
            "log_date": log_date,
            "weight_kg": weight,
            "body_fat_pct": body_fat,
            "waist_cm": waist,
            "arm_cm": arm,
            "thigh_cm": thigh,
            "note": note,
        })
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(f"[green]已记录 {log_date} 身体数据: {weight} kg / {body_fat}%[/green]")


@body_app.command()
def delete(
    log_date: str = typer.Option(
        ..., "--date", "-d", help="要删除的测量日期 (YYYY-MM-DD)"
    ),
) -> None:
    """删除指定日期的身体测量记录。"""
    console = get_console()
    try:
        date.fromisoformat(log_date)
    except ValueError as e:
        console.print(f"[red]日期格式无效 '{log_date}'。[/red]")
        raise typer.Exit(1) from e

    cli = get_client()
    try:
        logs = cli.list_body_logs()
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    target = next((r for r in logs if r["log_date"] == log_date), None)
    if target is None:
        console.print(f"[red]{log_date} 无记录。[/red]")
        raise typer.Exit(1)

    try:
        cli.delete_body_log(target["id"])
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(f"[green]已删除 {log_date} 身体测量记录。[/green]")


@body_app.command(name="list")
def list_body() -> None:
    """列出所有身体测量记录（按日期倒序）。"""
    console = get_console()
    cli = get_client()
    try:
        logs = cli.list_body_logs()
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    if not logs:
        console.print("[dim]暂无身体测量记录。[/dim]")
        return

    render_table(
        columns=["日期", "体重", "体脂率", "腰围", "臂围", "大腿围", "备注"],
        rows=[
            [
                str(r["log_date"]),
                f"{r['weight_kg']:.1f} kg",
                f"{r['body_fat_pct']:.1f}%",
                f"{r['waist_cm']:.1f}" if r.get("waist_cm") else "-",
                f"{r['arm_cm']:.1f}" if r.get("arm_cm") else "-",
                f"{r['thigh_cm']:.1f}" if r.get("thigh_cm") else "-",
                r.get("note") or "",
            ]
            for r in logs
        ],
        title="身体测量记录",
        align=["left", "right", "right", "right", "right", "right", "left"],
        col_styles=["cyan", "yellow", "", "", "", "", "dim"],
    )
