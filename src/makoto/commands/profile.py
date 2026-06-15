"""用户画像命令。"""

from __future__ import annotations

from datetime import date

import typer

from makoto.models.profile import ActivityLevel
from makoto.models.profile import Gender
from makoto.models.profile import UserProfile
from makoto.utils.console import get_console
from makoto.utils.console import render_table
from makoto.utils.profile_store import load
from makoto.utils.profile_store import save

profile_app = typer.Typer(no_args_is_help=True)


def _activity_choices() -> str:
    return ", ".join(a.value for a in ActivityLevel)


@profile_app.command()
def set(
    name: str = typer.Option(..., "--name", help="姓名"),
    gender: Gender = typer.Option(..., "--gender", help="性别 (male/female)"),
    age: int = typer.Option(..., "--age", min=1, max=120, help="年龄"),
    height: float = typer.Option(
        ..., "--height", min=0, help="身高（厘米）"
    ),
    weight: float = typer.Option(
        ..., "--weight", "-w", min=0, help="当前体重（公斤）"
    ),
    body_fat: float = typer.Option(
        ..., "--body-fat", "-b", min=0, max=60, help="体脂率（%）"
    ),
    target_weight: float = typer.Option(
        ..., "--target-weight", min=0, help="目标体重（公斤）"
    ),
    target_date: str = typer.Option(
        ..., "--target-date", help="目标达成日期 (YYYY-MM-DD)"
    ),
    activity: ActivityLevel = typer.Option(
        ..., "--activity", "-a", help=f"日常活动系数 ({_activity_choices()})"
    ),
) -> None:
    """设置或更新用户画像。"""
    console = get_console()
    try:
        parsed_date = date.fromisoformat(target_date)
    except ValueError as e:
        console.print(f"[red]日期格式无效 '{target_date}'，请使用 YYYY-MM-DD。[/red]")
        raise typer.Exit(1) from e

    profile = UserProfile(
        name=name,
        gender=gender,
        age=age,
        height_cm=height,
        weight_kg=weight,
        body_fat_pct=body_fat,
        target_weight_kg=target_weight,
        target_date=parsed_date,
        activity_level=activity,
    )
    save(profile)
    console.print(f"[green]用户画像已保存: {name}[/green]")


@profile_app.command()
def show() -> None:
    """查看用户画像与计算数据。"""
    console = get_console()
    profile = load()
    if profile is None:
        console.print("[dim]尚未设置用户画像，请使用 makoto profile set。[/dim]")
        return

    console.print(f"\n[bold cyan]{profile.name}[/bold cyan]")
    console.print(f"  性别:     {profile.gender.value}")
    console.print(f"  年龄:     {profile.age} 岁")
    console.print(f"  身高:     {profile.height_cm} cm")
    console.print(f"  体重:     {profile.weight_kg} kg")
    console.print(f"  体脂率:   {profile.body_fat_pct}%")
    console.print(f"  目标体重: {profile.target_weight_kg} kg")
    console.print(f"  目标日期: {profile.target_date}")
    console.print(f"  活动系数: {profile.activity_level.value}")

    # 计算指标
    deficit = profile.weekly_deficit_needed
    deficit_str = f"{deficit:.0f} kcal/周" if deficit is not None else "已过期"

    render_table(
        columns=["指标", "数值", "说明"],
        rows=[
            ["FFM (去脂体重)", f"{profile.ffm_kg:.1f} kg", "体重 × (1 - 体脂率)"],
            [
                "BMR (基础代谢)",
                f"{profile.bmr_kcal:.0f} kcal/天",
                "Mifflin-St Jeor 公式",
            ],
            [
                "REE (日常消耗)",
                f"{profile.ree_kcal:.0f} kcal/天",
                f"BMR × {profile.activity_level.multiplier} (不含运动)",
            ],
            [
                "每周缺口需求",
                deficit_str,
                f"距目标日 {(profile.target_date - date.today()).days} 天",
            ],
        ],
        title="计算结果",
        align=["left", "right", "left"],
        col_styles=["", "yellow", "dim"],
    )
