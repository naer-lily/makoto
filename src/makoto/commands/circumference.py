"""围度测量记录命令（CLI 客户端）。"""

from __future__ import annotations

from datetime import date
from typing import Any

import typer

from makoto.client.api import ClientError
from makoto.client.api import get_client
from makoto.utils.console import get_console
from makoto.utils.console import render_detail
from makoto.utils.console import render_table

circumference_app = typer.Typer(no_args_is_help=True)


def _fmt_cm(v: Any) -> str:
    """格式化围度数值，None 显示为占位符。"""
    return f"{float(v):.1f} cm" if v is not None else "—"


def _circumference_detail_fields(r: dict[str, Any]) -> list[tuple[str, str]]:
    """将一条围度测量记录展开为「字段 → 值」列表（详尽冗余）。

    Args:
        r: 服务端返回的围度测量记录字典（CircumferenceLogResponse）。

    Returns:
        供 render_detail 使用的 (字段名, 值) 列表。
    """
    note = r.get("note")
    return [
        ("记录 ID", str(r.get("id", ""))),
        ("测量日期", str(r.get("log_date", ""))),
        ("腰围", _fmt_cm(r.get("waist_cm"))),
        ("臂围", _fmt_cm(r.get("arm_cm"))),
        ("大腿围", _fmt_cm(r.get("thigh_cm"))),
        ("备注", str(note) if note else "—"),
        ("创建时间", str(r.get("created_at", ""))),
    ]


@circumference_app.command()
def log(
    log_date: str = typer.Option(
        ...,
        "--date",
        "-d",
        help="测量日期，格式 YYYY-MM-DD。每个日期仅允许一条记录（重复则服务端返回 409）。",
    ),
    waist: float | None = typer.Option(
        None, "--waist", min=0, help="腰围（厘米），可选，非负数。"
    ),
    arm: float | None = typer.Option(
        None, "--arm", min=0, help="臂围（厘米），可选，非负数。"
    ),
    thigh: float | None = typer.Option(
        None, "--thigh", min=0, help="大腿围（厘米），可选，非负数。"
    ),
    note: str | None = typer.Option(
        None, "--note", "-n", help="可选备注，自由文本。"
    ),
) -> None:
    """记录围度测量数据（每天仅一条，三围均可选）。

    成功后会打印这条记录的完整数据：记录 ID、测量日期、腰围、臂围、大腿围、
    备注与创建时间。
    """
    console = get_console()
    try:
        date.fromisoformat(log_date)
    except ValueError as e:
        console.print(f"[red]日期格式无效 '{log_date}'，请使用 YYYY-MM-DD。[/red]")
        raise typer.Exit(1) from e

    cli = get_client()
    try:
        result = cli.create_circumference_log({
            "log_date": log_date,
            "waist_cm": waist,
            "arm_cm": arm,
            "thigh_cm": thigh,
            "note": note,
        })
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(f"[green]已记录围度数据 #{result.get('id', '')}[/green]")
    render_detail("新增的围度测量记录", _circumference_detail_fields(result))


@circumference_app.command()
def delete(
    log_id: int = typer.Option(
        ...,
        "--id",
        "-i",
        min=1,
        help="要删除的围度测量记录 ID（整数）。可先用 'makoto circumference list' 查看 ID。",
    ),
) -> None:
    """按 ID 删除一条围度测量记录。

    成功后会打印被删除记录的完整数据，便于核对删除对象无误。
    记录不存在时服务端返回 404。
    """
    console = get_console()
    cli = get_client()
    try:
        deleted = cli.delete_circumference_log(log_id)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(f"[green]已删除围度测量记录 #{log_id}[/green]")
    render_detail("被删除的围度测量记录", _circumference_detail_fields(deleted))


@circumference_app.command(name="list")
def list_circumference(
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
) -> None:
    """列出围度测量记录（按日期倒序），可用 --start/--end 按日期前闭后闭过滤。

    表格首列为记录 ID，删除时直接用 'makoto circumference delete --id <ID>'。
    """
    console = get_console()
    cli = get_client()
    try:
        logs = cli.list_circumference_logs(start, end)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    if not logs:
        console.print("[dim]暂无围度测量记录。[/dim]")
        return

    render_table(
        columns=["ID", "日期", "腰围", "臂围", "大腿围", "备注"],
        rows=[
            [
                str(r.get("id", "")),
                str(r["log_date"]),
                f"{r['waist_cm']:.1f}" if r.get("waist_cm") else "-",
                f"{r['arm_cm']:.1f}" if r.get("arm_cm") else "-",
                f"{r['thigh_cm']:.1f}" if r.get("thigh_cm") else "-",
                r.get("note") or "",
            ]
            for r in logs
        ],
        title="围度测量记录",
        align=["right", "left", "right", "right", "right", "left"],
        col_styles=["magenta", "cyan", "yellow", "", "", "dim"],
    )
