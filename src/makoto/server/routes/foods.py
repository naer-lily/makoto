"""食物库 API 路由。"""

from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col
from sqlmodel import select

from makoto.server.auth import verify_token
from makoto.server.database import get_session
from makoto.server.db_models import DietLog
from makoto.server.db_models import Food
from makoto.server.models import FoodCreate
from makoto.server.models import FoodResponse
from makoto.server.models import FoodSearchResult
from makoto.utils.search import search_foods

router = APIRouter(prefix="/api/v1/foods", tags=["foods"])


def _to_response(row: Food) -> FoodResponse:
    assert row.id is not None
    return FoodResponse(
        id=row.id,
        name=row.name,
        calories_per_100g=row.calories_per_100g,
        protein_per_100g=row.protein_per_100g,
        carbs_per_100g=row.carbs_per_100g,
        fat_per_100g=row.fat_per_100g,
        search_keywords=json.loads(row.search_keywords),
        note=row.note,
        created_at=row.created_at or "",
    )


@router.get(
    "",
    response_model=list[FoodResponse],
    summary="列出所有食物",
    description="返回按名称排序的全部已注册食物及每100克营养数据。",
)
async def list_foods(
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> list[FoodResponse]:
    stmt = select(Food).order_by(col(Food.name))
    rows = (await session.execute(stmt)).scalars().all()
    return [_to_response(r) for r in rows]


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
    session: AsyncSession = Depends(get_session),
) -> FoodResponse:
    existing = (
        await session.execute(select(Food).where(Food.name == data.name))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"食物 '{data.name}' 已存在")

    row = Food(
        name=data.name,
        calories_per_100g=data.calories_per_100g,
        protein_per_100g=data.protein_per_100g,
        carbs_per_100g=data.carbs_per_100g,
        fat_per_100g=data.fat_per_100g,
        search_keywords=json.dumps(data.search_keywords, ensure_ascii=False),
        note=data.note,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _to_response(row)


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
    session: AsyncSession = Depends(get_session),
) -> list[FoodSearchResult]:
    rows = (await session.execute(select(Food))).scalars().all()
    if not rows:
        return []

    index: dict[str, list[str]] = {}
    id_map: dict[str, int] = {}
    for r in rows:
        assert r.id is not None
        index[r.name] = json.loads(r.search_keywords)
        id_map[r.name] = r.id

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
    session: AsyncSession = Depends(get_session),
) -> FoodResponse:
    row = (
        await session.execute(select(Food).where(Food.id == food_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="食物不存在")
    return _to_response(row)


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
    session: AsyncSession = Depends(get_session),
) -> FoodResponse:
    row = (
        await session.execute(select(Food).where(Food.id == food_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="食物不存在")

    old_name = row.name
    if data.name != old_name:
        dup = (
            await session.execute(select(Food).where(Food.name == data.name))
        ).scalar_one_or_none()
        if dup is not None:
            raise HTTPException(status_code=409, detail=f"食物 '{data.name}' 已存在")

    row.name = data.name
    row.calories_per_100g = data.calories_per_100g
    row.protein_per_100g = data.protein_per_100g
    row.carbs_per_100g = data.carbs_per_100g
    row.fat_per_100g = data.fat_per_100g
    row.search_keywords = json.dumps(data.search_keywords, ensure_ascii=False)
    row.note = data.note
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _to_response(row)


@router.delete(
    "/{food_id}",
    response_model=FoodResponse,
    summary="删除食物",
    description=(
        "从食物库中移除指定食物（若被饮食记录引用则拒绝），"
        "并在响应体中返回被删除食物的完整数据。"
    ),
)
async def delete_food(
    food_id: int,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> FoodResponse:
    row = (
        await session.execute(select(Food).where(Food.id == food_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="食物不存在")

    deleted = _to_response(row)
    referenced = (
        await session.execute(
            select(DietLog).where(DietLog.food_id == food_id).limit(1)
        )
    ).scalar_one_or_none()
    if referenced is not None:
        raise HTTPException(
            status_code=409,
            detail=f"食物 '{row.name}' 被饮食记录引用，无法删除",
        )

    await session.delete(row)
    await session.commit()
    return deleted
