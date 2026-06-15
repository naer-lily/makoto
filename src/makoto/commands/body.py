"""身体测量记录命令。"""

from __future__ import annotations

from datetime import date

import typer
from rich.table import Table

from makoto.models.records import BodyLog
from makoto.utils.console import get_console
from makoto.utils.data_paths import body_logs_path
from makoto.utils.jsonl_store import JsonlStore

body_app = typer.Typer(no_args_is_help=True)
store = JsonlStore(body_logs_path(), BodyLog)


@body_app.command()
def log(
    log_date: str = typer.Option(
        ..., "--date", "-d", help="测量日期 (YYYY-MM-DD)"
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
    """记录晨起身体测量数据。"""
    console = get_console()
    try:
        parsed_date = date.fromisoformat(log_date)
    except ValueError as e:
        console.print(f"[red]日期格式无效 '{log_date}'，请使用 YYYY-MM-DD。[/red]")
        raise typer.Exit(1) from e

    record = BodyLog(
        log_date=parsed_date,
        weight_kg=weight,
        body_fat_pct=body_fat,
        waist_cm=waist,
        arm_cm=arm,
        thigh_cm=thigh,
        note=note,
    )
    store.append(record)
    console.print(
        f"[green]已记录 {log_date} 身体数据: {weight} kg / {body_fat}%[/green]"
    )


@body_app.command(name="list")
def list_body() -> None:
    """列出所有身体测量记录（按日期倒序）。"""
    console = get_console()
    logs = store.read_all()
    logs.sort(key=lambda r: r.log_date, reverse=True)

    if not logs:
        console.print("[dim]暂无身体测量记录。[/dim]")
        return

    table = Table(title="身体测量记录")
    table.add_column("日期", style="cyan")
    table.add_column("体重", justify="right", style="yellow")
    table.add_column("体脂率", justify="right")
    table.add_column("腰围", justify="right")
    table.add_column("臂围", justify="right")
    table.add_column("大腿围", justify="right")
    table.add_column("备注", style="dim")

    for r in logs:
        table.add_row(
            str(r.log_date),
            f"{r.weight_kg:.1f} kg",
            f"{r.body_fat_pct:.1f}%",
            f"{r.waist_cm:.1f}" if r.waist_cm else "-",
            f"{r.arm_cm:.1f}" if r.arm_cm else "-",
            f"{r.thigh_cm:.1f}" if r.thigh_cm else "-",
            r.note or "",
        )

    console.print(table)
