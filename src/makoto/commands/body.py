"""身体测量记录命令。

每个日期仅允许一条记录（晨起空腹测量）。
"""

from __future__ import annotations

from datetime import date

import typer

from makoto.models.records import BodyLog
from makoto.utils.console import get_console
from makoto.utils.console import render_table
from makoto.utils.data_paths import body_logs_path
from makoto.utils.jsonl_store import JsonlStore

body_app = typer.Typer(no_args_is_help=True)
store = JsonlStore(body_logs_path(), BodyLog)


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
        parsed_date = date.fromisoformat(log_date)
    except ValueError as e:
        console.print(f"[red]日期格式无效 '{log_date}'，请使用 YYYY-MM-DD。[/red]")
        raise typer.Exit(1) from e

    if store.find_one(lambda r: r.log_date == parsed_date) is not None:
        console.print(
            f"[red]{log_date} 已有记录，请先 delete 再重新录入。[/red]"
        )
        raise typer.Exit(1)

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


@body_app.command()
def delete(
    log_date: str = typer.Option(
        ..., "--date", "-d", help="要删除的测量日期 (YYYY-MM-DD)"
    ),
) -> None:
    """删除指定日期的身体测量记录。"""
    console = get_console()
    try:
        parsed_date = date.fromisoformat(log_date)
    except ValueError as e:
        console.print(f"[red]日期格式无效 '{log_date}'。[/red]")
        raise typer.Exit(1) from e

    deleted = store.delete_many(lambda r: r.log_date == parsed_date)
    if deleted == 0:
        console.print(f"[red]{log_date} 无记录。[/red]")
        raise typer.Exit(1)

    console.print(f"[green]已删除 {log_date} 身体测量记录。[/green]")


@body_app.command(name="list")
def list_body() -> None:
    """列出所有身体测量记录（按日期倒序）。"""
    console = get_console()
    logs = store.read_all()
    logs.sort(key=lambda r: r.log_date, reverse=True)

    if not logs:
        console.print("[dim]暂无身体测量记录。[/dim]")
        return

    render_table(
        columns=["日期", "体重", "体脂率", "腰围", "臂围", "大腿围", "备注"],
        rows=[
            [
                str(r.log_date),
                f"{r.weight_kg:.1f} kg",
                f"{r.body_fat_pct:.1f}%",
                f"{r.waist_cm:.1f}" if r.waist_cm else "-",
                f"{r.arm_cm:.1f}" if r.arm_cm else "-",
                f"{r.thigh_cm:.1f}" if r.thigh_cm else "-",
                r.note or "",
            ]
            for r in logs
        ],
        title="身体测量记录",
        align=["left", "right", "right", "right", "right", "right", "left"],
        col_styles=["cyan", "yellow", "", "", "", "", "dim"],
    )
