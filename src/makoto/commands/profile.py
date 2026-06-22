"""用户画像命令（CLI 客户端）。"""

from __future__ import annotations

from datetime import date
from typing import Any

import typer

from makoto.client.api import ClientError
from makoto.client.api import get_client
from makoto.utils.console import get_console
from makoto.utils.console import render_detail
from makoto.utils.console import render_table

profile_app = typer.Typer(no_args_is_help=True)


def _profile_detail_fields(p: dict[str, Any]) -> list[tuple[str, str]]:
    """将用户画像展开为「字段 → 值」列表（详尽冗余，keep_token 脱敏）。

    Args:
        p: 服务端返回的画像字典（ProfileResponse）。

    Returns:
        供 render_detail 使用的 (字段名, 值) 列表。
    """
    deficit = p.get("weekly_deficit_needed")
    deficit_str = f"{deficit:.0f} kcal/周" if deficit is not None else "已过期"
    keep = "已配置" if p.get("keep_token") else "未配置"
    return [
        ("姓名", str(p.get("name", ""))),
        ("性别", str(p.get("gender", ""))),
        ("年龄", f"{p.get('age', '')} 岁"),
        ("身高", f"{p.get('height_cm', '')} cm"),
        ("体重", f"{p.get('weight_kg', '')} kg"),
        ("体脂率", f"{p.get('body_fat_pct', '')} %"),
        ("目标体重", f"{p.get('target_weight_kg', '')} kg"),
        ("目标日期", str(p.get("target_date", ""))),
        ("活动系数", str(p.get("activity_level", ""))),
        ("Keep 令牌", keep),
        ("── 推算指标 ──", ""),
        ("FFM (去脂体重)", f"{float(p.get('ffm_kg', 0)):.1f} kg"),
        ("BMR (基础代谢)", f"{float(p.get('bmr_kcal', 0)):.1f} kcal/天"),
        ("REE (日常消耗)", f"{float(p.get('ree_kcal', 0)):.1f} kcal/天"),
        ("每周缺口需求", deficit_str),
        ("距目标日剩余", f"{p.get('days_remaining', 0)} 天"),
    ]


@profile_app.command()
def set(
    name: str = typer.Option(..., "--name", help="姓名，自由文本。"),
    gender: str = typer.Option(
        ..., "--gender", help="性别，取值 'male' 或 'female'。"
    ),
    age: int = typer.Option(..., "--age", min=1, max=120, help="年龄（岁），取值 1-120。"),
    height: float = typer.Option(
        ..., "--height", min=0, help="身高（厘米），非负数。"
    ),
    weight: float = typer.Option(
        ..., "--weight", "-w", min=0, help="当前体重（公斤），非负数。"
    ),
    body_fat: float = typer.Option(
        ..., "--body-fat", "-b", min=0, max=60, help="体脂率（百分比），取值 0-60。"
    ),
    target_weight: float = typer.Option(
        ..., "--target-weight", min=0, help="目标体重（公斤），非负数。"
    ),
    target_date: str = typer.Option(
        ..., "--target-date", help="目标达成日期，格式 YYYY-MM-DD。"
    ),
    activity: str = typer.Option(
        ...,
        "--activity",
        "-a",
        help=(
            "日常活动系数，取值之一："
            "sedentary / light / moderate / active / very_active。"
        ),
    ),
) -> None:
    """设置或更新用户画像（覆盖式写入）。

    成功后会打印完整画像，包括录入的基本信息与据此推算的
    FFM、BMR、REE、每周缺口需求、距目标日剩余天数。
    """
    console = get_console()
    try:
        date.fromisoformat(target_date)
    except ValueError as e:
        console.print(f"[red]日期格式无效 '{target_date}'，请使用 YYYY-MM-DD。[/red]")
        raise typer.Exit(1) from e

    cli = get_client()
    try:
        result = cli.set_profile({
            "name": name,
            "gender": gender,
            "age": age,
            "height_cm": height,
            "weight_kg": weight,
            "body_fat_pct": body_fat,
            "target_weight_kg": target_weight,
            "target_date": target_date,
            "activity_level": activity,
        })
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(f"[green]用户画像已保存: {name}[/green]")
    render_detail("当前用户画像", _profile_detail_fields(result))


@profile_app.command()
def show() -> None:
    """查看用户画像与据此推算的代谢、缺口等计算数据。"""
    console = get_console()
    cli = get_client()
    try:
        p = cli.get_profile()
    except ClientError as e:
        if e.status == 404:
            console.print("[dim]尚未设置用户画像，请使用 makoto profile set。[/dim]")
            return
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(f"\n[bold cyan]{p['name']}[/bold cyan]")
    console.print(f"  性别:     {p['gender']}")
    console.print(f"  年龄:     {p['age']} 岁")
    console.print(f"  身高:     {p['height_cm']} cm")
    console.print(f"  体重:     {p['weight_kg']} kg")
    console.print(f"  体脂率:   {p['body_fat_pct']}%")
    console.print(f"  目标体重: {p['target_weight_kg']} kg")
    console.print(f"  目标日期: {p['target_date']}")
    console.print(f"  活动系数: {p['activity_level']}")

    deficit = p.get("weekly_deficit_needed")
    deficit_str = f"{deficit:.0f} kcal/周" if deficit is not None else "已过期"
    days_remaining = p.get("days_remaining", 0)

    render_table(
        columns=["指标", "数值", "说明"],
        rows=[
            ["FFM (去脂体重)", f"{p['ffm_kg']:.1f} kg", "体重 x (1 - 体脂率)"],
            ["BMR (基础代谢)", f"{p['bmr_kcal']:.1f} kcal/天", "Mifflin-St Jeor 公式"],
            [
                "REE (日常消耗)",
                f"{p['ree_kcal']:.1f} kcal/天",
                f"BMR x {p['activity_level']} (不含运动)",
            ],
            ["每周缺口需求", deficit_str, f"距目标日 {days_remaining} 天"],
        ],
        title="计算结果",
        align=["left", "right", "left"],
        col_styles=["", "yellow", "dim"],
    )
