"""食物管理命令（CLI 客户端）。"""

from __future__ import annotations

import typer

from makoto.client.api import ClientError
from makoto.client.api import get_client
from makoto.server.models import nutrition_for
from makoto.utils.console import get_console
from makoto.utils.console import render_table

food_app = typer.Typer(no_args_is_help=True)


@food_app.command()
def add(
    name: str = typer.Argument(..., help="食物名称（唯一标识）"),
    calories: float = typer.Option(
        ..., "--calories", "-c", min=0, help="每 100 克热量（千卡）"
    ),
    protein: float = typer.Option(
        ..., "--protein", "-p", min=0, help="每 100 克蛋白质（克）"
    ),
    carbs: float = typer.Option(..., "--carbs", min=0, help="每 100 克碳水（克）"),
    fat: float = typer.Option(..., "--fat", "-f", min=0, help="每 100 克脂肪（克）"),
    keywords: str | None = typer.Option(
        None, "--keywords", "-k", help="搜索关键词，逗号分隔"
    ),
    note: str | None = typer.Option(None, "--note", "-n", help="备注"),
) -> None:
    """注册一种新食物。"""
    console = get_console()
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []
    cli = get_client()
    try:
        cli.add_food({
            "name": name,
            "calories_per_100g": calories,
            "protein_per_100g": protein,
            "carbs_per_100g": carbs,
            "fat_per_100g": fat,
            "search_keywords": kw_list,
            "note": note,
        })
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e
    console.print(f"[green]已注册食物: {name}[/green]")


@food_app.command()
def delete(
    name: str = typer.Argument(..., help="要删除的食物名称"),
) -> None:
    """删除已注册的食物。"""
    console = get_console()
    cli = get_client()
    try:
        foods = cli.list_foods()
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    target = next((f for f in foods if f["name"] == name), None)
    if target is None:
        console.print(f"[red]食物 '{name}' 不存在。[/red]")
        raise typer.Exit(1)

    try:
        cli.delete_food(target["id"])
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e
    console.print(f"[green]已删除食物: {name}[/green]")


@food_app.command(name="list")
def list_foods() -> None:
    """列出所有已注册食物。"""
    console = get_console()
    cli = get_client()
    try:
        foods = cli.list_foods()
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    if not foods:
        console.print("[dim]暂无已注册食物。[/dim]")
        return

    render_table(
        columns=["名称", "热量/100g", "蛋白质/100g", "碳水/100g", "脂肪/100g", "关键词"],
        rows=[
            [
                f["name"],
                f"{f['calories_per_100g']:.0f} kcal",
                f"{f['protein_per_100g']:.1f} g",
                f"{f['carbs_per_100g']:.1f} g",
                f"{f['fat_per_100g']:.1f} g",
                ", ".join(f.get("search_keywords", [])),
            ]
            for f in foods
        ],
        title="食物库",
        align=["left", "right", "right", "right", "right", "left"],
        col_styles=["cyan", "yellow", "", "", "", "dim"],
    )


@food_app.command()
def show(
    name: str = typer.Argument(..., help="食物名称"),
) -> None:
    """查看食物详细营养信息。"""
    console = get_console()
    cli = get_client()
    try:
        foods = cli.list_foods()
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    target = next((f for f in foods if f["name"] == name), None)
    if target is None:
        console.print(f"[red]未找到食物 '{name}'。[/red]")
        raise typer.Exit(1)

    f = target
    console.print(f"\n[bold cyan]{f['name']}[/bold cyan]")
    console.print(f"  每 100g 热量:     {f['calories_per_100g']:.0f} kcal")
    console.print(f"  每 100g 蛋白质:   {f['protein_per_100g']:.1f} g")
    console.print(f"  每 100g 碳水:     {f['carbs_per_100g']:.1f} g")
    console.print(f"  每 100g 脂肪:     {f['fat_per_100g']:.1f} g")
    if f.get("search_keywords"):
        console.print(f"  关键词:           {', '.join(f['search_keywords'])}")
    if f.get("note"):
        console.print(f"  备注:             {f['note']}")

    console.print("\n[bold]常见份量参考:[/bold]")
    ref_rows: list[list[str]] = []
    for grams in [50, 100, 150, 200, 250, 300]:
        n = nutrition_for(
            float(f["calories_per_100g"]),
            float(f["protein_per_100g"]),
            float(f["carbs_per_100g"]),
            float(f["fat_per_100g"]),
            grams,
        )
        ref_rows.append([
            str(grams),
            f"{n['calories_kcal']:.0f} kcal",
            f"{n['protein_g']:.1f} g",
            f"{n['carbs_g']:.1f} g",
            f"{n['fat_g']:.1f} g",
        ])

    render_table(
        columns=["克数", "热量", "蛋白质", "碳水", "脂肪"],
        rows=ref_rows,
        align=["right", "right", "right", "right", "right"],
        col_styles=["", "yellow", "", "", ""],
    )


@food_app.command()
def search(
    query: str = typer.Argument(..., help="搜索词"),
    limit: int = typer.Option(20, "--limit", "-n", help="最大返回数量"),
) -> None:
    """模糊搜索食物（按名称和关键词）。"""
    console = get_console()
    cli = get_client()
    try:
        results = cli.search_foods(query, limit)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    if not results:
        console.print(f"[dim]未找到与 '{query}' 相关的食物。[/dim]")
        return

    console.print(f"\n[bold]搜索 '{query}' 结果（按相似度排序）:[/bold]\n")
    render_table(
        columns=["#", "名称", "编辑距离"],
        rows=[
            [str(i), r["name"], str(r["distance"])]
            for i, r in enumerate(results, 1)
        ],
        align=["right", "left", "right"],
        col_styles=["dim", "cyan", ""],
    )
