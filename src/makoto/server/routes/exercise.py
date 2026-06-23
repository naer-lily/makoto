"""运动记录 API 路由。

同分钟不可重复。
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
from makoto.server.db_models import ExerciseLog
from makoto.server.models import ExerciseLogCreate
from makoto.server.models import ExerciseLogResponse
from makoto.utils.tz import to_store_str

router = APIRouter(prefix="/api/v1/exercise-logs", tags=["exercise"])


def _to_response(row: ExerciseLog) -> ExerciseLogResponse:
    assert row.id is not None
    return ExerciseLogResponse(
        id=row.id,
        log_time=datetime.fromisoformat(row.log_time),
        exercise_name=row.exercise_name,
        duration_desc=row.duration_desc,
        calories_kcal=row.calories_kcal,
        note=row.note,
        created_at=row.created_at or "",
    )


@router.get(
    "",
    response_model=list[ExerciseLogResponse],
    summary="列出运动记录",
    description=(
        "按时间倒序返回运动记录，包含运动名称、时长描述和消耗热量。"
        "支持 start/end 按日期前闭后闭过滤。"
    ),
)
async def list_exercise_logs(
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
) -> list[ExerciseLogResponse]:
    stmt = select(ExerciseLog)
    if start is not None:
        stmt = stmt.where(func.date(col(ExerciseLog.log_time)) >= func.date(start))
    if end is not None:
        stmt = stmt.where(func.date(col(ExerciseLog.log_time)) <= func.date(end))
    stmt = stmt.order_by(col(ExerciseLog.log_time).desc()).limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    return [_to_response(r) for r in rows]


@router.post(
    "",
    response_model=ExerciseLogResponse,
    status_code=201,
    summary="记录一次运动",
    description="记录一次运动消耗（同分钟不可重复）。",
)
async def create_exercise_log(
    data: ExerciseLogCreate,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> ExerciseLogResponse:
    time_str = to_store_str(data.log_time)
    existing = (
        await session.execute(
            select(ExerciseLog).where(ExerciseLog.log_time == time_str)
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"{time_str} 已有记录，请错开至少 1 分钟")

    row = ExerciseLog(
        log_time=time_str,
        exercise_name=data.exercise_name,
        duration_desc=data.duration_desc,
        calories_kcal=data.calories_kcal,
        note=data.note,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _to_response(row)


@router.put(
    "/{log_id}",
    response_model=ExerciseLogResponse,
    summary="更新运动记录",
    description="修改运动记录的名称、时长、消耗热量、备注或时间。同分钟不可重复（排除自身）。",
)
async def update_exercise_log(
    log_id: int,
    data: ExerciseLogCreate,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> ExerciseLogResponse:
    row = (
        await session.execute(select(ExerciseLog).where(ExerciseLog.id == log_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="记录不存在")

    time_str = to_store_str(data.log_time)
    dup = (
        await session.execute(
            select(ExerciseLog).where(
                ExerciseLog.log_time == time_str, ExerciseLog.id != log_id
            )
        )
    ).scalar_one_or_none()
    if dup is not None:
        raise HTTPException(status_code=409, detail=f"{time_str} 已有记录，请错开至少 1 分钟")

    row.log_time = time_str
    row.exercise_name = data.exercise_name
    row.duration_desc = data.duration_desc
    row.calories_kcal = data.calories_kcal
    row.note = data.note
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _to_response(row)


@router.delete(
    "/{log_id}",
    response_model=ExerciseLogResponse,
    summary="删除运动记录",
    description="删除指定的运动记录，并在响应体中返回被删除记录的完整数据。",
)
async def delete_exercise_log(
    log_id: int,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> ExerciseLogResponse:
    row = (
        await session.execute(select(ExerciseLog).where(ExerciseLog.id == log_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    deleted = _to_response(row)
    await session.delete(row)
    await session.commit()
    return deleted
