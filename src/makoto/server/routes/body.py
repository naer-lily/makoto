"""身体测量 API 路由。

每个日期仅允许一条记录，录入后自动同步画像。
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
from makoto.server.db_models import BodyLog
from makoto.server.db_models import Profile
from makoto.server.models import BodyLogCreate
from makoto.server.models import BodyLogResponse

router = APIRouter(prefix="/api/v1/body-logs", tags=["body"])


def _to_response(row: BodyLog) -> BodyLogResponse:
    assert row.id is not None
    return BodyLogResponse(
        id=row.id,
        log_date=date.fromisoformat(row.log_date),
        weight_kg=row.weight_kg,
        body_fat_pct=row.body_fat_pct,
        note=row.note,
        created_at=row.created_at or "",
    )


@router.get(
    "",
    response_model=list[BodyLogResponse],
    summary="列出身体测量记录",
    description=(
        "按日期倒序返回身体测量记录，包含体重、体脂率。"
        "支持 start/end 按日期前闭后闭过滤。"
    ),
)
async def list_body_logs(
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
) -> list[BodyLogResponse]:
    stmt = select(BodyLog)
    if start is not None:
        stmt = stmt.where(func.date(col(BodyLog.log_date)) >= func.date(start))
    if end is not None:
        stmt = stmt.where(func.date(col(BodyLog.log_date)) <= func.date(end))
    stmt = stmt.order_by(col(BodyLog.log_date).desc())
    rows = (await session.execute(stmt)).scalars().all()
    return [_to_response(r) for r in rows]


@router.post(
    "",
    response_model=BodyLogResponse,
    status_code=201,
    summary="记录身体测量数据",
    description="录入当日的身体测量数据（每日仅一条），录入后自动同步画像中的体重和体脂率。",
)
async def create_body_log(
    data: BodyLogCreate,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> BodyLogResponse:
    date_str = data.log_date.isoformat()
    existing = (
        await session.execute(select(BodyLog).where(BodyLog.log_date == date_str))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"{date_str} 已有记录")

    row = BodyLog(
        log_date=date_str,
        weight_kg=data.weight_kg,
        body_fat_pct=data.body_fat_pct,
        note=data.note,
    )
    session.add(row)

    profile = (
        await session.execute(select(Profile).where(Profile.id == 1))
    ).scalar_one_or_none()
    if profile is not None:
        profile.weight_kg = data.weight_kg
        profile.body_fat_pct = data.body_fat_pct
        session.add(profile)

    await session.commit()
    await session.refresh(row)
    return _to_response(row)


@router.delete(
    "/{log_id}",
    response_model=BodyLogResponse,
    summary="删除身体测量记录",
    description="删除指定的身体测量记录，并在响应体中返回被删除记录的完整数据。",
)
async def delete_body_log(
    log_id: int,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> BodyLogResponse:
    row = (
        await session.execute(select(BodyLog).where(BodyLog.id == log_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    deleted = _to_response(row)
    await session.delete(row)
    await session.commit()
    return deleted
