"""食物管理命令。"""

from __future__ import annotations

import typer

from makoto.models.records import Food
from makoto.utils.console import get_console
from makoto.utils.console import render_table
from makoto.utils.data_paths import foods_path
from makoto.utils.jsonl_store import JsonlStore
from makoto.utils.search import search_foods as do_search

food_app = typer.Typer(no_args_is_help=True)
store = JsonlStore(foods_path(), Food)


def _build_index() -> dict[str, list[str]]:
    """构建搜索索引：{name: keywords}。"""
    index: dict[str, list[str]] = {}
    for food in store.read_all():
        index[food.name] = food.search_keywords
    return index


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
    if store.find_one(lambda f: f.name == name):
        console.print(f"[red]食物 '{name}' 已存在。[/red]")
        raise typer.Exit(1)

    kw_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []
    food = Food(
        name=name,
        calories_per_100g=calories,
        protein_per_100g=protein,
        carbs_per_100g=carbs,
        fat_per_100g=fat,
        search_keywords=kw_list,
        note=note,
    )
    store.append(food)
    console.print(f"[green]已注册食物: {name}[/green]")


@food_app.command()
def delete(
    name: str = typer.Argument(..., help="要删除的食物名称"),
) -> None:
    """删除已注册的食物。"""
    console = get_console()
    if store.find_one(lambda f: f.name == name) is None:
        console.print(f"[red]食物 '{name}' 不存在。[/red]")
        raise typer.Exit(1)

    store.delete_many(lambda f: f.name == name)
    console.print(f"[green]已删除食物: {name}[/green]")


@food_app.command(name="list")
def list_foods() -> None:
    """列出所有已注册食物。"""
    console = get_console()
    foods = store.read_all()
    if not foods:
        console.print("[dim]暂无已注册食物。[/dim]")
        return

    render_table(
        columns=["名称", "热量/100g", "蛋白质/100g", "碳水/100g", "脂肪/100g", "关键词"],
        rows=[
            [
                f.name,
                f"{f.calories_per_100g:.0f} kcal",
                f"{f.protein_per_100g:.1f} g",
                f"{f.carbs_per_100g:.1f} g",
                f"{f.fat_per_100g:.1f} g",
                ", ".join(f.search_keywords),
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
    food = store.find_one(lambda f: f.name == name)
    if food is None:
        console.print(f"[red]未找到食物 '{name}'。[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]{food.name}[/bold cyan]")
    console.print(f"  每 100g 热量:     {food.calories_per_100g:.0f} kcal")
    console.print(f"  每 100g 蛋白质:   {food.protein_per_100g:.1f} g")
    console.print(f"  每 100g 碳水:     {food.carbs_per_100g:.1f} g")
    console.print(f"  每 100g 脂肪:     {food.fat_per_100g:.1f} g")
    if food.search_keywords:
        console.print(f"  关键词:           {', '.join(food.search_keywords)}")
    if food.note:
        console.print(f"  备注:             {food.note}")

    console.print("\n[bold]常见份量参考:[/bold]")
    ref_rows: list[list[str]] = []
    for grams in [50, 100, 150, 200, 250, 300]:
        n = food.nutrition_for(grams)
        ref_rows.append([
            f"{grams}",
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
    index = _build_index()
    if not index:
        console.print("[dim]食物库为空，请先注册食物。[/dim]")
        return

    results = do_search(query, index, max_results=limit)
    if not results:
        console.print(f"[dim]未找到与 '{query}' 相关的食物。[/dim]")
        return

    console.print(f"\n[bold]搜索 '{query}' 结果（按相似度排序）:[/bold]\n")
    render_table(
        columns=["#", "名称", "编辑距离"],
        rows=[
            [str(i), name, str(dist)]
            for i, (dist, name) in enumerate(results, 1)
        ],
        align=["right", "left", "right"],
        col_styles=["dim", "cyan", ""],
    )
