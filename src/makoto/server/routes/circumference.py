"""围度测量 API 路由。

每个日期仅允许一条记录，三围均为可选字段。
"""

from __future__ import annotations

from datetime import date

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
from makoto.server.db_models import CircumferenceLog
from makoto.server.models import CircumferenceLogCreate
from makoto.server.models import CircumferenceLogResponse

router = APIRouter(prefix="/api/v1/circumference-logs", tags=["circumference"])


def _to_response(row: CircumferenceLog) -> CircumferenceLogResponse:
    assert row.id is not None
    return CircumferenceLogResponse(
        id=row.id,
        log_date=date.fromisoformat(row.log_date),
        waist_cm=row.waist_cm,
        arm_cm=row.arm_cm,
        thigh_cm=row.thigh_cm,
        note=row.note,
        created_at=row.created_at or "",
    )


@router.get(
    "",
    response_model=list[CircumferenceLogResponse],
    summary="列出围度测量记录",
    description=(
        "按日期倒序返回围度测量记录。支持 start/end 按日期前闭后闭过滤。"
    ),
)
async def list_circumference_logs(
    start: str | None = Query(
        None,
        description="起始日期 YYYY-MM-DD（前闭，含当天）。省略表示不限下界。",
    ),
    end: str | None = Query(
        None,
        description="结束日期 YYYY-MM-DD（后闭，含当天）。省略表示不限上界。",
    ),
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> list[CircumferenceLogResponse]:
    stmt = select(CircumferenceLog)
    if start is not None:
        stmt = stmt.where(func.date(col(CircumferenceLog.log_date)) >= func.date(start))
    if end is not None:
        stmt = stmt.where(func.date(col(CircumferenceLog.log_date)) <= func.date(end))
    stmt = stmt.order_by(col(CircumferenceLog.log_date).desc())
    rows = (await session.execute(stmt)).scalars().all()
    return [_to_response(r) for r in rows]


@router.post(
    "",
    response_model=CircumferenceLogResponse,
    status_code=201,
    summary="记录围度测量数据",
    description="录入当日的围度测量数据（每日仅一条）。三围全部可选。",
)
async def create_circumference_log(
    data: CircumferenceLogCreate,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> CircumferenceLogResponse:
    date_str = data.log_date.isoformat()
    existing = (
        await session.execute(
            select(CircumferenceLog).where(CircumferenceLog.log_date == date_str)
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"{date_str} 已有围度记录")

    row = CircumferenceLog(
        log_date=date_str,
        waist_cm=data.waist_cm,
        arm_cm=data.arm_cm,
        thigh_cm=data.thigh_cm,
        note=data.note,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _to_response(row)


@router.delete(
    "/{log_id}",
    response_model=CircumferenceLogResponse,
    summary="删除围度测量记录",
    description="删除指定的围度测量记录，并在响应体中返回被删除记录的完整数据。",
)
async def delete_circumference_log(
    log_id: int,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> CircumferenceLogResponse:
    row = (
        await session.execute(
            select(CircumferenceLog).where(CircumferenceLog.id == log_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    deleted = _to_response(row)
    await session.delete(row)
    await session.commit()
    return deleted
