"""绘画会话记录 API 路由。

每次绘画心跳/自动保存一条，同一天允许多条记录。
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
from makoto.server.db_models import PaintingLog
from makoto.server.models import PaintingLogCreate
from makoto.server.models import PaintingLogResponse
from makoto.utils.tz import to_store_str

router = APIRouter(prefix="/api/v1/painting-logs", tags=["painting"])


def _to_response(row: PaintingLog) -> PaintingLogResponse:
    assert row.id is not None
    return PaintingLogResponse(
        id=row.id,
        log_time=datetime.fromisoformat(row.log_time),
        file_path=row.file_path,
        file_id=row.file_id,
        duration_seconds=row.duration_seconds,
        note=row.note,
        created_at=row.created_at or "",
    )


@router.get(
    "",
    response_model=list[PaintingLogResponse],
    summary="列出绘画会话记录",
    description=(
        "按时间倒序返回绘画会话记录，包含文件路径、文件 ID 和绘画时长（秒）。"
        "支持 start/end 按日期前闭后闭过滤。"
    ),
)
async def list_painting_logs(
    start: str | None = Query(
        None,
        description="起始日期 YYYY-MM-DD（前闭，含当天）。省略表示不限下界。",
    ),
    end: str | None = Query(
        None,
        description="结束日期 YYYY-MM-DD（后闭，含当天）。省略表示不限上界。",
    ),
    limit: int = Query(200, ge=1, le=2000, description="最大返回条数，范围 1-2000。"),
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> list[PaintingLogResponse]:
    stmt = select(PaintingLog)
    if start is not None:
        stmt = stmt.where(func.date(col(PaintingLog.log_time)) >= func.date(start))
    if end is not None:
        stmt = stmt.where(func.date(col(PaintingLog.log_time)) <= func.date(end))
    stmt = stmt.order_by(col(PaintingLog.log_time).desc()).limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    return [_to_response(r) for r in rows]


@router.post(
    "",
    response_model=PaintingLogResponse,
    status_code=201,
    summary="记录一次绘画会话",
    description="记录一次绘画会话（不检查唯一性，同天允许多条）。",
)
async def create_painting_log(
    data: PaintingLogCreate,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> PaintingLogResponse:
    row = PaintingLog(
        log_time=to_store_str(data.log_time),
        file_path=data.file_path,
        file_id=data.file_id,
        duration_seconds=data.duration_seconds,
        note=data.note,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _to_response(row)


@router.put(
    "/{log_id}",
    response_model=PaintingLogResponse,
    summary="更新绘画会话记录",
    description="修改绘画会话的时间、文件、时长或备注。",
)
async def update_painting_log(
    log_id: int,
    data: PaintingLogCreate,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> PaintingLogResponse:
    row = (
        await session.execute(select(PaintingLog).where(PaintingLog.id == log_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="记录不存在")

    row.log_time = to_store_str(data.log_time)
    row.file_path = data.file_path
    row.file_id = data.file_id
    row.duration_seconds = data.duration_seconds
    row.note = data.note
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _to_response(row)


@router.delete(
    "/{log_id}",
    response_model=PaintingLogResponse,
    summary="删除绘画会话记录",
    description="删除指定的绘画会话记录，并在响应体中返回被删除记录的完整数据。",
)
async def delete_painting_log(
    log_id: int,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> PaintingLogResponse:
    row = (
        await session.execute(select(PaintingLog).where(PaintingLog.id == log_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    deleted = _to_response(row)
    await session.delete(row)
    await session.commit()
    return deleted
