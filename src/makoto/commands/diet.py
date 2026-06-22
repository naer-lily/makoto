"""饮食记录命令（CLI 客户端）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import typer

from makoto.client.api import ClientError
from makoto.client.api import get_client
from makoto.utils.console import get_console
from makoto.utils.console import render_detail
from makoto.utils.console import render_table
from makoto.utils.tz import ensure_aware
from makoto.utils.tz import to_store_str

diet_app = typer.Typer(no_args_is_help=True)


def _diet_detail_fields(r: dict[str, Any]) -> list[tuple[str, str]]:
    """将一条饮食记录展开为「字段 → 值」列表（详尽冗余）。

    包含记录本身、该食物每 100g 基准营养、本次克数对应营养三段。

    Args:
        r: 服务端返回的饮食记录字典（DietLogResponse）。

    Returns:
        供 render_detail 使用的 (字段名, 值) 列表。
    """
    note = r.get("note")
    return [
        ("记录 ID", str(r.get("id", ""))),
        ("进餐时间", str(r.get("log_time", ""))),
        ("食物名称", str(r.get("food_name", ""))),
        ("摄入克数", f"{float(r.get('grams', 0)):.0f} g"),
        ("备注", str(note) if note else "—"),
        ("── 食物每 100g 基准 ──", ""),
        ("基准热量", f"{float(r.get('food_calories_per_100g', 0)):.0f} kcal/100g"),
        ("基准蛋白质", f"{float(r.get('food_protein_per_100g', 0)):.1f} g/100g"),
        ("基准碳水", f"{float(r.get('food_carbs_per_100g', 0)):.1f} g/100g"),
        ("基准脂肪", f"{float(r.get('food_fat_per_100g', 0)):.1f} g/100g"),
        ("── 本次摄入营养 ──", ""),
        ("热量", f"{float(r.get('calories_kcal', 0)):.0f} kcal"),
        ("蛋白质", f"{float(r.get('protein_g', 0)):.1f} g"),
        ("碳水", f"{float(r.get('carbs_g', 0)):.1f} g"),
        ("脂肪", f"{float(r.get('fat_g', 0)):.1f} g"),
        ("创建时间", str(r.get("created_at", ""))),
    ]


@diet_app.command()
def log(
    log_time: datetime = typer.Option(
        ...,
        "--time",
        "-t",
        formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"],
        help=(
            "进餐时间，格式 'YYYY-MM-DDTHH:MM' 或 'YYYY-MM-DD HH:MM'。"
            "同一分钟不可重复记录（若冲突服务端返回 409）。无时区时按服务端时区处理。"
        ),
    ),
    food_name: str = typer.Option(
        ...,
        "--food",
        "-f",
        help="食物名称，必须已在食物库中注册（否则服务端返回 404）。用于自动计算营养。",
    ),
    grams: float = typer.Option(
        ...,
        "--grams",
        "-g",
        min=0,
        help="本次摄入克数（克），用于按食物每 100g 基准换算热量与营养素。",
    ),
    note: str | None = typer.Option(
        None, "--note", "-n", help="可选备注，自由文本，例如「早餐」「加蛋」。"
    ),
) -> None:
    """记录一次饮食摄入（同一分钟不可重复）。

    成功后会打印这条记录的完整数据：记录 ID、进餐时间、食物名称、克数、备注，
    所选食物每 100g 的基准营养，以及本次克数对应的热量/蛋白质/碳水/脂肪。
    """
    console = get_console()
    log_time_aware = ensure_aware(log_time)
    cli = get_client()
    try:
        result = cli.create_diet_log({
            "log_time": to_store_str(log_time_aware),
            "food_name": food_name,
            "grams": grams,
            "note": note,
        })
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(f"[green]已记录饮食 #{result.get('id', '')}[/green]")
    render_detail("新增的饮食记录", _diet_detail_fields(result))


@diet_app.command()
def delete(
    log_id: int = typer.Option(
        ...,
        "--id",
        "-i",
        min=1,
        help="要删除的饮食记录 ID（整数）。可先用 'makoto diet list' 查看每条记录的 ID。",
    ),
) -> None:
    """按 ID 删除一条饮食记录。

    成功后会打印被删除记录的完整数据（记录 ID、时间、食物、克数、营养等），
    便于核对删除对象无误。记录不存在时服务端返回 404。
    """
    console = get_console()
    cli = get_client()
    try:
        deleted = cli.delete_diet_log(log_id)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(f"[green]已删除饮食记录 #{log_id}[/green]")
    render_detail("被删除的饮食记录", _diet_detail_fields(deleted))


@diet_app.command(name="list")
def list_diet(
    start: str | None = typer.Option(
        None,
        "--start",
        "-s",
        help=(
            "起始日期 YYYY-MM-DD（前闭，含当天）。与 --end 组成前闭后闭区间；"
            "省略则不限下界。"
        ),
    ),
    end: str | None = typer.Option(
        None,
        "--end",
        "-e",
        help=(
            "结束日期 YYYY-MM-DD（后闭，含当天）。与 --start 组成前闭后闭区间；"
            "省略则不限上界。"
        ),
    ),
    limit: int = typer.Option(
        50, "--limit", "-n", min=1, max=500, help="最大显示条数（按时间倒序），范围 1-500。"
    ),
) -> None:
    """列出饮食记录（按时间倒序），可用 --start/--end 按日期前闭后闭过滤。

    表格首列为记录 ID，删除时直接用 'makoto diet delete --id <ID>'。
    """
    console = get_console()
    cli = get_client()
    try:
        logs = cli.list_diet_logs(limit, start, end)
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
            str(r.get("id", "")),
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
        columns=["ID", "时间", "食物", "克数", "热量", "蛋白质", "碳水", "脂肪", "备注"],
        rows=rows,
        title="饮食记录",
        align=["right", "left", "left", "right", "right", "right", "right", "right", "left"],
        col_styles=["magenta", "cyan", "green", "", "yellow", "", "", "", "dim"],
    )

    console.print(f"[bold]显示 {len(logs)} 条，合计 {total_cal:.0f} kcal[/bold]")
