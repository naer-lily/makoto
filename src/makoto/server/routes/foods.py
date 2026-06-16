"""食物库 API 路由。"""

from __future__ import annotations

import json

import aiosqlite
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from makoto.server.auth import verify_token
from makoto.server.database import get_db
from makoto.server.models import FoodCreate
from makoto.server.models import FoodResponse
from makoto.server.models import FoodSearchResult
from makoto.utils.search import search_foods

router = APIRouter(prefix="/api/v1/foods", tags=["foods"])


def _row_to_response(row: aiosqlite.Row) -> FoodResponse:
    d = dict(row)
    return FoodResponse(
        id=int(d["id"]),
        name=str(d["name"]),
        calories_per_100g=float(d["calories_per_100g"]),
        protein_per_100g=float(d["protein_per_100g"]),
        carbs_per_100g=float(d["carbs_per_100g"]),
        fat_per_100g=float(d["fat_per_100g"]),
        search_keywords=json.loads(str(d["search_keywords"])),
        note=str(d["note"]) if d["note"] else None,
        created_at=str(d["created_at"]),
    )


@router.get(
    "",
    response_model=list[FoodResponse],
    summary="列出所有食物",
    description="返回按名称排序的全部已注册食物及每100克营养数据。",
)
async def list_foods(
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[FoodResponse]:
    cursor = await db.execute("SELECT * FROM food ORDER BY name")
    rows = await cursor.fetchall()
    return [_row_to_response(r) for r in rows]


@router.post(
    "",
    response_model=FoodResponse,
    status_code=201,
    summary="注册新食物",
    description="向食物库中添加一种新食物，包含每100克的营养成分数据和搜索关键词。",
)
async def add_food(
    data: FoodCreate,
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> FoodResponse:
    cursor = await db.execute("SELECT id FROM food WHERE name = ?", (data.name,))
    if await cursor.fetchone():
        raise HTTPException(status_code=409, detail=f"食物 '{data.name}' 已存在")

    cursor = await db.execute(
        """INSERT INTO food (name, calories_per_100g, protein_per_100g,
           carbs_per_100g, fat_per_100g, search_keywords, note)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            data.name,
            data.calories_per_100g,
            data.protein_per_100g,
            data.carbs_per_100g,
            data.fat_per_100g,
            json.dumps(data.search_keywords, ensure_ascii=False),
            data.note,
        ),
    )
    await db.commit()
    food_id = cursor.lastrowid
    cursor2 = await db.execute("SELECT * FROM food WHERE id = ?", (food_id,))
    row = await cursor2.fetchone()
    assert row is not None
    return _row_to_response(row)


@router.get(
    "/search",
    response_model=list[FoodSearchResult],
    summary="模糊搜索食物",
    description="按名称和关键词进行模糊匹配，返回匹配的食物列表及编辑距离。",
)
async def search_food(
    q: str = Query(..., description="搜索词"),
    limit: int = Query(20, ge=1, le=100),
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[FoodSearchResult]:
    cursor = await db.execute("SELECT id, name, search_keywords FROM food")
    rows = await cursor.fetchall()
    if not rows:
        return []

    index: dict[str, list[str]] = {}
    id_map: dict[str, int] = {}
    for r in rows:
        d = dict(r)
        name = str(d["name"])
        index[name] = json.loads(str(d["search_keywords"]))
        id_map[name] = int(d["id"])

    results = search_foods(q, index, max_results=limit)
    return [
        FoodSearchResult(id=id_map[name], name=name, distance=dist)
        for dist, name in results
    ]


@router.get(
    "/{food_id}",
    response_model=FoodResponse,
    summary="查看食物详情",
    description="根据食物 ID 返回某一种食物的完整信息。",
)
async def get_food(
    food_id: int,
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> FoodResponse:
    cursor = await db.execute("SELECT * FROM food WHERE id = ?", (food_id,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="食物不存在")
    return _row_to_response(row)


@router.put(
    "/{food_id}",
    response_model=FoodResponse,
    summary="更新食物信息",
    description="修改食物名称或营养成分。若名称变更，同步更新所有引用该食物的饮食记录。",
)
async def update_food(
    food_id: int,
    data: FoodCreate,
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> FoodResponse:
    cursor = await db.execute("SELECT * FROM food WHERE id = ?", (food_id,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="食物不存在")

    old_name = str(dict(row)["name"])
    if data.name != old_name:
        cursor2 = await db.execute("SELECT id FROM food WHERE name = ?", (data.name,))
        if await cursor2.fetchone():
            raise HTTPException(status_code=409, detail=f"食物 '{data.name}' 已存在")
        await db.execute(
            "UPDATE diet_log SET food_name = ? WHERE food_name = ?",
            (data.name, old_name),
        )

    await db.execute(
        """UPDATE food SET name=?, calories_per_100g=?, protein_per_100g=?,
           carbs_per_100g=?, fat_per_100g=?, search_keywords=?, note=?
           WHERE id=?""",
        (
            data.name,
            data.calories_per_100g,
            data.protein_per_100g,
            data.carbs_per_100g,
            data.fat_per_100g,
            json.dumps(data.search_keywords, ensure_ascii=False),
            data.note,
            food_id,
        ),
    )
    await db.commit()

    cursor3 = await db.execute("SELECT * FROM food WHERE id = ?", (food_id,))
    row3 = await cursor3.fetchone()
    assert row3 is not None
    return _row_to_response(row3)


@router.delete(
    "/{food_id}",
    summary="删除食物",
    description="从食物库中移除指定食物（若被饮食记录引用则拒绝）。",
)
async def delete_food(
    food_id: int,
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, str]:
    cursor = await db.execute("SELECT id, name FROM food WHERE id = ?", (food_id,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="食物不存在")

    d = dict(row)
    old_name = str(d["name"])
    cursor2 = await db.execute(
        "SELECT COUNT(*) AS cnt FROM diet_log WHERE food_name = ?", (old_name,)
    )
    count_row = await cursor2.fetchone()
    if count_row and int(dict(count_row)["cnt"]) > 0:
        raise HTTPException(
            status_code=409,
            detail=f"食物 '{old_name}' 被饮食记录引用，无法删除",
        )

    await db.execute("DELETE FROM food WHERE id = ?", (food_id,))
    await db.commit()
    return {"detail": "已删除"}
