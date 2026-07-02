"""绘画会话记录命令（CLI 客户端）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import typer

from makoto.client.api import ClientError
from makoto.client.api import get_client
from makoto.utils.console import get_console
from makoto.utils.console import render_detail
from makoto.utils.console import render_table

painting_app = typer.Typer(no_args_is_help=True)


def _seconds_to_display(seconds: float) -> str:
    """将秒数转为人类可读的显示字符串。"""
    if seconds < 60:
        return f"{seconds:.0f} 秒"
    if seconds < 3600:
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m} 分 {s} 秒"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return f"{h} 小时 {m} 分"


def _painting_detail_fields(r: dict[str, Any]) -> list[tuple[str, str]]:
    note = r.get("note")
    return [
        ("记录 ID", str(r.get("id", ""))),
        ("绘画时间", str(r.get("log_time", ""))),
        ("文件 ID", str(r.get("file_id", ""))),
        ("文件路径", str(r.get("file_path", ""))),
        ("绘画时长", _seconds_to_display(float(r.get("duration_seconds", 0)))),
        ("备注", str(note) if note else "—"),
        ("创建时间", str(r.get("created_at", ""))),
    ]


@painting_app.command()
def log(
    log_time: str = typer.Option(
        ...,
        "--time",
        "-t",
        help="绘画时间，格式 YYYY-MM-DDTHH:MM:SS。",
    ),
    file_path: str = typer.Option(
        ...,
        "--path",
        "-p",
        help="绘画文件的完整路径，如 D:/ART/xxx.kra。",
    ),
    duration_seconds: float = typer.Option(
        ...,
        "--duration",
        "-d",
        min=0,
        help="该次会话的绘画时长（秒）。",
    ),
    file_id: str | None = typer.Option(
        None,
        "--file-id",
        "-f",
        help="文件的唯一标识（如 UUID）。",
    ),
    note: str | None = typer.Option(
        None,
        "--note",
        "-n",
        help="可选备注。",
    ),
) -> None:
    """记录一次绘画会话。同一文件同一天允许多条记录。"""
    console = get_console()
    try:
        datetime.fromisoformat(log_time)
    except ValueError as e:
        console.print(f"[red]时间格式无效 '{log_time}'，请使用 YYYY-MM-DDTHH:MM:SS。[/red]")
        raise typer.Exit(1) from e

    cli = get_client()
    try:
        result = cli.create_painting_log({
            "log_time": log_time,
            "file_path": file_path,
            "file_id": file_id if file_id else "",
            "duration_seconds": duration_seconds,
            "note": note,
        })
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(f"[green]已记录绘画会话 #{result.get('id', '')}[/green]")
    render_detail("新增的绘画会话", _painting_detail_fields(result))


@painting_app.command()
def delete(
    log_id: int = typer.Option(
        ...,
        "--id",
        "-i",
        min=1,
        help="要删除的绘画会话记录 ID。可先用 'makoto painting list' 查看每条记录的 ID。",
    ),
) -> None:
    """按 ID 删除一条绘画会话记录。"""
    console = get_console()
    cli = get_client()
    try:
        deleted = cli.delete_painting_log(log_id)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(f"[green]已删除绘画会话记录 #{log_id}[/green]")
    render_detail("被删除的绘画会话", _painting_detail_fields(deleted))


@painting_app.command(name="list")
def list_painting(
    start: str | None = typer.Option(
        None,
        "--start",
        "-s",
        help="起始日期 YYYY-MM-DD（前闭，含当天）。",
    ),
    end: str | None = typer.Option(
        None,
        "--end",
        "-e",
        help="结束日期 YYYY-MM-DD（后闭，含当天）。",
    ),
    limit: int = typer.Option(
        200,
        "--limit",
        "-n",
        min=1,
        max=2000,
        help="最大返回条数。",
    ),
) -> None:
    """列出绘画会话记录（按时间倒序）。"""
    console = get_console()
    cli = get_client()
    try:
        logs = cli.list_painting_logs(start, end, limit)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    if not logs:
        console.print("[dim]暂无绘画记录。[/dim]")
        return

    rows: list[list[str]] = []
    for r in logs:
        rows.append([
            str(r.get("id", "")),
            str(r.get("log_time", "")),
            str(r.get("file_id", "")),
            _seconds_to_display(float(r.get("duration_seconds", 0))),
            r.get("note") or "",
        ])

    render_table(
        columns=["ID", "绘画时间", "文件 ID", "时长", "备注"],
        rows=rows,
        title="绘画会话记录",
        align=["right", "left", "left", "right", "left"],
        col_styles=["magenta", "cyan", "green", "yellow", "dim"],
    )

    # 统计汇总
    unique_dates = {r.get("log_time", "")[:10] for r in logs if r.get("log_time")}
    total_seconds = sum(float(r.get("duration_seconds", 0)) for r in logs)
    console.print(
        f"[bold]显示 {len(logs)} 条，涉及 {len(unique_dates)} 天，"
        f"合计 {_seconds_to_display(total_seconds)}[/bold]"
    )


@painting_app.command()
def update(
    log_id: int = typer.Option(
        ...,
        "--id",
        "-i",
        min=1,
        help="要更新的绘画会话记录 ID。",
    ),
    log_time: str | None = typer.Option(
        None,
        "--time",
        "-t",
        help="绘画时间，格式 YYYY-MM-DDTHH:MM:SS。",
    ),
    file_path: str | None = typer.Option(
        None,
        "--path",
        "-p",
        help="绘画文件的完整路径。",
    ),
    file_id: str | None = typer.Option(
        None,
        "--file-id",
        "-f",
        help="文件的唯一标识（如 UUID）。",
    ),
    duration_seconds: float | None = typer.Option(
        None,
        "--duration",
        "-d",
        min=0,
        help="绘画时长（秒）。",
    ),
    note: str | None = typer.Option(
        None,
        "--note",
        "-n",
        help="备注。",
    ),
) -> None:
    """更新一条绘画会话记录。所有字段可选，仅更新传入的部分。"""
    console = get_console()
    cli = get_client()

    try:
        existing_list = cli.list_painting_logs(limit=2000)
        existing = next((r for r in existing_list if r.get("id") == log_id), None)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    if existing is None:
        console.print(f"[red]绘画会话记录 #{log_id} 不存在。[/red]")
        raise typer.Exit(1)

    if log_time is not None:
        try:
            datetime.fromisoformat(log_time)
        except ValueError as e:
            console.print(f"[red]时间格式无效 '{log_time}'，请使用 YYYY-MM-DDTHH:MM:SS。[/red]")
            raise typer.Exit(1) from e

    resolved_file_id = file_id if file_id else existing.get("file_id", "")

    payload: dict[str, object] = {
        "log_time": log_time if log_time is not None else existing.get("log_time", ""),
        "file_path": file_path if file_path is not None else existing.get("file_path", ""),
        "file_id": resolved_file_id,
        "duration_seconds": (
            duration_seconds if duration_seconds is not None
            else existing.get("duration_seconds", 0)
        ),
        "note": note if note is not None else existing.get("note"),
    }

    try:
        result = cli.update_painting_log(log_id, payload)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(f"[green]已更新绘画会话记录 #{log_id}[/green]")
    render_detail("更新后的绘画会话", _painting_detail_fields(result))
