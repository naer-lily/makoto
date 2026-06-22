"""运动记录命令（CLI 客户端）。"""

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

exercise_app = typer.Typer(no_args_is_help=True)


def _exercise_detail_fields(r: dict[str, Any]) -> list[tuple[str, str]]:
    """将一条运动记录展开为「字段 → 值」列表（详尽冗余）。

    Args:
        r: 服务端返回的运动记录字典（ExerciseLogResponse）。

    Returns:
        供 render_detail 使用的 (字段名, 值) 列表。
    """
    note = r.get("note")
    return [
        ("记录 ID", str(r.get("id", ""))),
        ("运动时间", str(r.get("log_time", ""))),
        ("运动名称", str(r.get("exercise_name", ""))),
        ("时长/数量", str(r.get("duration_desc", ""))),
        ("消耗热量", f"{float(r.get('calories_kcal', 0)):.0f} kcal"),
        ("备注", str(note) if note else "—"),
        ("创建时间", str(r.get("created_at", ""))),
    ]


@exercise_app.command()
def log(
    log_time: datetime = typer.Option(
        ...,
        "--time",
        "-t",
        formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"],
        help=(
            "运动时间，格式 'YYYY-MM-DDTHH:MM' 或 'YYYY-MM-DD HH:MM'。"
            "同一分钟不可重复记录（若冲突服务端返回 409）。无时区时按服务端时区处理。"
        ),
    ),
    name: str = typer.Option(
        ..., "--name", "-n", help="运动名称，自由文本，例如「跑步」「卧推」。"
    ),
    duration: str = typer.Option(
        ...,
        "--duration",
        "-d",
        help="时长 / 组数 / 数量描述，自由文本，例如「30 分钟」「4 组 x 12」。",
    ),
    calories: float = typer.Option(
        ..., "--calories", "-c", min=0, help="本次运动消耗热量（千卡），需为非负数。"
    ),
    note: str | None = typer.Option(
        None, "--note", help="可选备注，自由文本。"
    ),
) -> None:
    """记录一次运动消耗（同一分钟不可重复）。

    成功后会打印这条记录的完整数据：记录 ID、运动时间、名称、时长/数量、
    消耗热量、备注与创建时间。
    """
    console = get_console()
    log_time_aware = ensure_aware(log_time)
    cli = get_client()
    try:
        result = cli.create_exercise_log({
            "log_time": to_store_str(log_time_aware),
            "exercise_name": name,
            "duration_desc": duration,
            "calories_kcal": calories,
            "note": note,
        })
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(f"[green]已记录运动 #{result.get('id', '')}[/green]")
    render_detail("新增的运动记录", _exercise_detail_fields(result))


@exercise_app.command()
def delete(
    log_id: int = typer.Option(
        ...,
        "--id",
        "-i",
        min=1,
        help="要删除的运动记录 ID（整数）。可先用 'makoto exercise list' 查看每条记录的 ID。",
    ),
) -> None:
    """按 ID 删除一条运动记录。

    成功后会打印被删除记录的完整数据，便于核对删除对象无误。
    记录不存在时服务端返回 404。
    """
    console = get_console()
    cli = get_client()
    try:
        deleted = cli.delete_exercise_log(log_id)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(f"[green]已删除运动记录 #{log_id}[/green]")
    render_detail("被删除的运动记录", _exercise_detail_fields(deleted))


@exercise_app.command(name="list")
def list_exercise(
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
    """列出运动记录（按时间倒序），可用 --start/--end 按日期前闭后闭过滤。

    表格首列为记录 ID，删除时直接用 'makoto exercise delete --id <ID>'。
    """
    console = get_console()
    cli = get_client()
    try:
        logs = cli.list_exercise_logs(limit, start, end)
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
            str(r.get("id", "")),
            str(r.get("log_time", "")),
            str(r.get("exercise_name", "")),
            str(r.get("duration_desc", "")),
            f"{cal:.0f} kcal",
            r.get("note") or "",
        ])

    render_table(
        columns=["ID", "时间", "运动", "时长/数量", "消耗热量", "备注"],
        rows=rows,
        title="运动记录",
        align=["right", "left", "left", "left", "right", "left"],
        col_styles=["magenta", "cyan", "green", "", "yellow", "dim"],
    )

    console.print(f"[bold]显示 {len(logs)} 条，合计 {total_cal:.0f} kcal[/bold]")
