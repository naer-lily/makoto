"""饮食记录 API 路由。

同分钟不可重复，记录时自动计算营养素。食物通过 food_id 外键关联。
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col
from sqlmodel import select

from makoto.server.auth import verify_token
from makoto.server.database import get_session
from makoto.server.db_models import DietLog
from makoto.server.db_models import Food
from makoto.server.models import DietLogCreate
from makoto.server.models import DietLogResponse
from makoto.server.models import DietLogUpdate
from makoto.server.models import nutrition_for
from makoto.utils.tz import to_store_str

router = APIRouter(prefix="/api/v1/diet-logs", tags=["diet"])


async def _food_by_id(session: AsyncSession, food_id: int) -> Food | None:
    return (
        await session.execute(select(Food).where(Food.id == food_id))
    ).scalar_one_or_none()


async def _to_response(session: AsyncSession, row: DietLog) -> DietLogResponse:
    """构造饮食记录响应（含食物名称与营养，外键保证食物存在）。"""
    assert row.id is not None
    food = await _food_by_id(session, row.food_id)
    if food is None:
        name, base_cal, base_pro, base_carb, base_fat = "", 0.0, 0.0, 0.0, 0.0
    else:
        name = food.name
        base_cal = food.calories_per_100g
        base_pro = food.protein_per_100g
        base_carb = food.carbs_per_100g
        base_fat = food.fat_per_100g
    n = nutrition_for(base_cal, base_pro, base_carb, base_fat, row.grams)
    return DietLogResponse(
        id=row.id,
        log_time=datetime.fromisoformat(row.log_time),
        food_id=row.food_id,
        food_name=name,
        grams=row.grams,
        note=row.note,
        calories_kcal=n["calories_kcal"],
        protein_g=n["protein_g"],
        carbs_g=n["carbs_g"],
        fat_g=n["fat_g"],
        food_calories_per_100g=base_cal,
        food_protein_per_100g=base_pro,
        food_carbs_per_100g=base_carb,
        food_fat_per_100g=base_fat,
        created_at=row.created_at or "",
    )


@router.get(
    "",
    response_model=list[DietLogResponse],
    summary="列出饮食记录",
    description=(
        "按时间倒序返回饮食记录，包含食物 id/名称、克数、自动计算的营养素，"
        "以及该食物每 100g 的基准营养。支持 start/end 按日期前闭后闭过滤。"
    ),
)
async def list_diet_logs(
    start: str | None = Query(
        None,
        description="起始日期 YYYY-MM-DD（前闭，含当天）。省略表示不限下界。",
    ),
    end: str | None = Query(
        None,
        description="结束日期 YYYY-MM-DD（后闭，含当天）。省略表示不限上界。",
    ),
    limit: int = Query(50, ge=1, le=500, description="最大返回条数，范围 1-500。"),
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> list[DietLogResponse]:
    stmt = select(DietLog)
    if start is not None:
        stmt = stmt.where(func.date(col(DietLog.log_time)) >= func.date(start))
    if end is not None:
        stmt = stmt.where(func.date(col(DietLog.log_time)) <= func.date(end))
    stmt = stmt.order_by(col(DietLog.log_time).desc()).limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    return [await _to_response(session, r) for r in rows]


@router.post(
    "",
    response_model=DietLogResponse,
    status_code=201,
    summary="记录一次饮食",
    description="记录一次饮食摄入（同分钟不可重复），自动根据食物库中的营养数据计算热量和营养素。",
)
async def create_diet_log(
    data: DietLogCreate,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> DietLogResponse:
    time_str = to_store_str(data.log_time)

    food = await _food_by_id(session, data.food_id)
    if food is None:
        raise HTTPException(status_code=404, detail=f"食物 id={data.food_id} 未注册")

    dup = (
        await session.execute(select(DietLog).where(DietLog.log_time == time_str))
    ).scalar_one_or_none()
    if dup is not None:
        raise HTTPException(status_code=409, detail=f"{time_str} 已有记录，请错开至少 1 分钟")

    row = DietLog(
        log_time=time_str,
        food_id=data.food_id,
        grams=data.grams,
        note=data.note,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return await _to_response(session, row)


@router.put(
    "/{log_id}",
    response_model=DietLogResponse,
    summary="更新饮食记录",
    description="修改饮食记录的食物、克数、备注或时间。食物必须已在食物库中注册。",
)
async def update_diet_log(
    log_id: int,
    data: DietLogUpdate,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> DietLogResponse:
    row = (
        await session.execute(select(DietLog).where(DietLog.id == log_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="记录不存在")

    food = await _food_by_id(session, data.food_id)
    if food is None:
        raise HTTPException(status_code=404, detail=f"食物 id={data.food_id} 未注册")

    time_str = to_store_str(data.log_time)
    dup = (
        await session.execute(
            select(DietLog).where(
                DietLog.log_time == time_str, DietLog.id != log_id
            )
        )
    ).scalar_one_or_none()
    if dup is not None:
        raise HTTPException(status_code=409, detail=f"{time_str} 已有记录，请错开至少 1 分钟")

    row.log_time = time_str
    row.food_id = data.food_id
    row.grams = data.grams
    row.note = data.note
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return await _to_response(session, row)


@router.delete(
    "/{log_id}",
    response_model=DietLogResponse,
    summary="删除饮食记录",
    description="删除指定的饮食记录，并在响应体中返回被删除记录的完整数据（含营养与食物基准）。",
)
async def delete_diet_log(
    log_id: int,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> DietLogResponse:
    row = (
        await session.execute(select(DietLog).where(DietLog.id == log_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    deleted = await _to_response(session, row)
    await session.delete(row)
    await session.commit()
    return deleted
