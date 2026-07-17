"""天气监视命令（CLI 客户端）。"""

from __future__ import annotations

from typing import Any

import typer

from makoto.client.api import ClientError
from makoto.client.api import get_client
from makoto.utils.console import get_console
from makoto.utils.console import render_table

weather_app = typer.Typer(no_args_is_help=True)
watch_app = typer.Typer(no_args_is_help=True, help="监视地点管理")
weather_app.add_typer(watch_app, name="watch")


# ── 监视地点 ──


@watch_app.command(name="list")
def list_watches() -> None:
    """列出所有天气监视地点。"""
    console = get_console()
    cli = get_client()
    try:
        watches = cli.list_weather_watches()
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    if not watches:
        console.print("[dim]暂无监视地点。[/dim]")
        return

    render_table(
        columns=["ID", "标签", "纬度", "经度"],
        rows=[
            [str(w["id"]), str(w["label"]), f"{w['latitude']:.4f}", f"{w['longitude']:.4f}"]
            for w in watches
        ],
        title="天气监视地点",
        align=["right", "left", "right", "right"],
        col_styles=["magenta", "cyan", "", ""],
    )


@watch_app.command()
def add(
    label: str = typer.Argument(..., help="地点名称，例如 '北京' 或 '香山'。"),
    lat: float = typer.Option(..., "--lat", "-a", min=-90, max=90, help="纬度。"),
    lon: float = typer.Option(..., "--lon", "-o", min=-180, max=180, help="经度。"),
) -> None:
    """新增天气监视地点（同时拉取首次预报）。"""
    console = get_console()
    cli = get_client()
    try:
        result = cli.add_weather_watch({"label": label, "latitude": lat, "longitude": lon})
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(f"[green]已添加监视地点 #{result['id']}: {label} ({lat}, {lon})[/green]")


@watch_app.command()
def update(
    watch_id: int = typer.Option(..., "--id", "-i", help="监视地点 ID。"),
    label: str | None = typer.Option(None, "--label", "-l", help="新地点名称。"),
    lat: float | None = typer.Option(None, "--lat", "-a", help="新纬度。"),
    lon: float | None = typer.Option(None, "--lon", "-o", help="新经度。"),
) -> None:
    """修改监视地点（至少提供一个字段）。"""
    console = get_console()
    data: dict[str, object] = {}
    if label is not None:
        data["label"] = label
    if lat is not None:
        data["latitude"] = lat
    if lon is not None:
        data["longitude"] = lon
    if not data:
        console.print("[red]请至少提供 --label、--lat 或 --lon 中的一个。[/red]")
        raise typer.Exit(1)

    cli = get_client()
    try:
        result = cli.update_weather_watch(watch_id, data)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(
        f"[green]已更新 #{result['id']}: {result['label']} "
        f"({result['latitude']}, {result['longitude']})[/green]"
    )


@watch_app.command()
def delete(
    watch_id: int = typer.Option(..., "--id", "-i", help="要删除的监视地点 ID。"),
) -> None:
    """删除监视地点。"""
    console = get_console()
    cli = get_client()
    try:
        result = cli.delete_weather_watch(watch_id)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(f"[green]已删除 #{result['id']}: {result['label']}[/green]")


# ── 天气查询 ──


def _render_forecast(fc: dict[str, Any]) -> None:
    """渲染单个地点的天气预报表格。"""
    label = fc.get("label", "?")
    fetched = fc.get("fetched_at", "?")

    rows: list[list[str]] = []
    for day in fc.get("days", []):
        code = day.get("weather_code", 0)
        desc = day.get("weather_desc", "")
        # 雷暴高亮
        if code in (95, 96, 99):
            desc = f"[red bold]{desc}[/red bold]"
        precip = day.get("precip_sum", 0.0)
        prob = day.get("precip_probability", 0)
        rows.append([
            str(day.get("date", "")),
            f"{day.get('temp_max', 0):.0f} / {day.get('temp_min', 0):.0f} °C",
            f"{precip:.1f} mm",
            f"{prob}%",
            str(code),
            desc,
        ])

    title = (
        f"{label} ({fc.get('latitude', 0):.2f}, {fc.get('longitude', 0):.2f})"
        f" — 缓存时间: {fetched}"
    )
    render_table(
        columns=["日期", "温度(高/低)", "降水", "概率", "WMO", "天气"],
        rows=rows,
        title=title,
        align=["left", "right", "right", "right", "right", "left"],
        col_styles=["cyan", "yellow", "", "", "", ""],
    )


@weather_app.command()
def forecast(
    watch_id: int | None = typer.Argument(None, help="监视地点 ID，不传则显示所有地点。"),
    refresh: bool = typer.Option(False, "--refresh", "-r", help="强制重新拉取天气数据。"),
) -> None:
    """查看天气缓存预报（默认返回缓存，--refresh 强制刷新）。"""
    console = get_console()
    cli = get_client()
    try:
        result = cli.weather_forecast(watch_id=watch_id, refresh=refresh)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    items: list[dict[str, Any]] = [result] if isinstance(result, dict) else result

    if not items:
        console.print("[dim]暂无天气数据，请先添加监视地点。[/dim]")
        return

    for fc in items:
        if fc.get("days"):
            _render_forecast(fc)
        else:
            label = fc.get("label", "?")
            console.print(f"\n[dim]{label} — 暂无缓存数据（等待后台拉取）[/dim]")
