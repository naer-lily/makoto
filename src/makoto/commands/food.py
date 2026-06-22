"""食物管理命令（CLI 客户端）。"""

from __future__ import annotations

from typing import Any

import typer

from makoto.client.api import ClientError
from makoto.client.api import get_client
from makoto.server.models import nutrition_for
from makoto.utils.console import get_console
from makoto.utils.console import render_detail
from makoto.utils.console import render_table

food_app = typer.Typer(no_args_is_help=True)


def _food_detail_fields(f: dict[str, Any]) -> list[tuple[str, str]]:
    """将一种食物展开为「字段 → 值」列表（详尽冗余）。

    Args:
        f: 服务端返回的食物字典（FoodResponse）。

    Returns:
        供 render_detail 使用的 (字段名, 值) 列表。
    """
    note = f.get("note")
    keywords = f.get("search_keywords") or []
    return [
        ("食物 ID", str(f.get("id", ""))),
        ("名称", str(f.get("name", ""))),
        ("热量/100g", f"{float(f.get('calories_per_100g', 0)):.0f} kcal"),
        ("蛋白质/100g", f"{float(f.get('protein_per_100g', 0)):.1f} g"),
        ("碳水/100g", f"{float(f.get('carbs_per_100g', 0)):.1f} g"),
        ("脂肪/100g", f"{float(f.get('fat_per_100g', 0)):.1f} g"),
        ("搜索关键词", ", ".join(keywords) if keywords else "—"),
        ("备注", str(note) if note else "—"),
        ("创建时间", str(f.get("created_at", ""))),
    ]


@food_app.command()
def add(
    name: str = typer.Argument(
        ..., help="食物名称，作为食物库中的唯一标识（重复则服务端返回 409）。"
    ),
    calories: float = typer.Option(
        ..., "--calories", "-c", min=0, help="每 100 克热量（千卡），非负数。"
    ),
    protein: float = typer.Option(
        ..., "--protein", "-p", min=0, help="每 100 克蛋白质（克），非负数。"
    ),
    carbs: float = typer.Option(
        ..., "--carbs", min=0, help="每 100 克碳水化合物（克），非负数。"
    ),
    fat: float = typer.Option(
        ..., "--fat", "-f", min=0, help="每 100 克脂肪（克），非负数。"
    ),
    keywords: str | None = typer.Option(
        None,
        "--keywords",
        "-k",
        help="搜索关键词，多个以英文逗号分隔，用于模糊搜索，例如 'rice,糙米'。",
    ),
    note: str | None = typer.Option(
        None, "--note", "-n", help="可选备注，自由文本。"
    ),
) -> None:
    """注册一种新食物（名称唯一）。

    成功后会打印这种食物的完整数据：食物 ID、名称、每 100g 各营养素、
    搜索关键词、备注与创建时间。
    """
    console = get_console()
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []
    cli = get_client()
    try:
        result = cli.add_food({
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

    console.print(f"[green]已注册食物 #{result.get('id', '')}: {name}[/green]")
    render_detail("新增的食物", _food_detail_fields(result))


@food_app.command()
def delete(
    food_id: int = typer.Option(
        ...,
        "--id",
        "-i",
        min=1,
        help="要删除的食物 ID（整数）。可先用 'makoto food list' 查看每种食物的 ID。",
    ),
) -> None:
    """按 ID 删除已注册的食物。

    成功后会打印被删除食物的完整数据，便于核对删除对象无误。
    食物不存在时返回 404；若该食物已被饮食记录引用则返回 409 拒绝删除。
    """
    console = get_console()
    cli = get_client()
    try:
        deleted = cli.delete_food(food_id)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(f"[green]已删除食物 #{food_id}: {deleted.get('name', '')}[/green]")
    render_detail("被删除的食物", _food_detail_fields(deleted))


@food_app.command(name="list")
def list_foods() -> None:
    """列出所有已注册食物（按名称排序）。

    表格首列为食物 ID，删除时直接用 'makoto food delete --id <ID>'。
    """
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
        columns=["ID", "名称", "热量/100g", "蛋白质/100g", "碳水/100g", "脂肪/100g", "关键词"],
        rows=[
            [
                str(f.get("id", "")),
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
        align=["right", "left", "right", "right", "right", "right", "left"],
        col_styles=["magenta", "cyan", "yellow", "", "", "", "dim"],
    )


@food_app.command()
def show(
    name: str = typer.Argument(..., help="要查看的食物名称（须与食物库中名称完全一致）。"),
) -> None:
    """查看某种食物的详细营养信息与常见份量换算参考表。"""
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
    render_detail(f"食物 #{f.get('id', '')}", _food_detail_fields(f))

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
    query: str = typer.Argument(..., help="搜索词，按食物名称与关键词做模糊匹配。"),
    limit: int = typer.Option(
        20, "--limit", "-n", min=1, max=100, help="最大返回数量，范围 1-100。"
    ),
) -> None:
    """模糊搜索食物（按名称和关键词），结果按编辑距离升序排列。

    结果含食物 ID，可直接用于 'makoto food delete --id <ID>'。
    """
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
        columns=["ID", "名称", "编辑距离"],
        rows=[
            [str(r.get("id", "")), r["name"], str(r["distance"])]
            for r in results
        ],
        align=["right", "left", "right"],
        col_styles=["magenta", "cyan", ""],
    )
