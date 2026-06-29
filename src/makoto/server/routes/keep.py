"""Keep 运动数据代理路由。

从用户画像中的 keep_token 读取 Keep API 凭证，
代理请求体能水平、周运动负荷等图表数据。
返回干净字段名（无 Keep 内部 $ 别名）。
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from makoto.server.auth import verify_token
from makoto.server.database import get_session
from makoto.server.db_models import Profile
from makoto.server.keep_client import FitnessQuery
from makoto.server.keep_client import Keep
from makoto.server.keep_client import WeeklyLoadQuery

router = APIRouter(prefix="/api/v1/keep", tags=["keep"])


class FitnessResponse(BaseModel):
    """体能水平 — 单日 ATL / CTL / TSB。"""

    date: str
    atl: int
    ctl: int
    tsb: int


class WeeklyLoadResponse(BaseModel):
    """周运动负荷 — 单周训练负荷与推荐区间。"""

    user_id: str
    week_start: str
    training_load: int | None
    load_lower: int
    load_upper: int


async def _get_keep_token(session: AsyncSession) -> str | None:
    row = (
        await session.execute(select(Profile).where(Profile.id == 1))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="用户画像未设置")
    return row.keep_token or None


@router.get(
    "/fitness",
    response_model=list[FitnessResponse],
    summary="体能水平 (ATL/CTL/TSB)",
)
async def get_fitness(
    start_date: str | None = Query(default=None, description="起始日期 YYYY-MM-DD"),
    end_date: str | None = Query(default=None, description="结束日期 YYYY-MM-DD"),
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> list[FitnessResponse]:
    keep_token = await _get_keep_token(session)
    if not keep_token:
        return []
    q: FitnessQuery | None = None
    if start_date or end_date:
        ds = start_date.replace("-", ".") if start_date else ""
        de = end_date.replace("-", ".") if end_date else ""
        label = ""
        if start_date and end_date:
            s = date.fromisoformat(start_date)
            e = date.fromisoformat(end_date)
            days = (e - s).days + 1
            label = f"近{days}天"
        elif start_date:
            label = ds
        elif end_date:
            label = de
        q = FitnessQuery(date_start=ds, date_end=de, date_label=label)
    async with Keep(token=keep_token) as k:
        records = await k.get_fitness(q)
    return [
        FitnessResponse(date=r.date, atl=r.atl, ctl=r.ctl, tsb=r.tsb)
        for r in records
    ]


@router.get(
    "/weekly-load",
    response_model=list[WeeklyLoadResponse],
    summary="周运动负荷",
)
async def get_weekly_load(
    week_count: int | None = Query(default=None, description="近 N 周"),
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> list[WeeklyLoadResponse]:
    keep_token = await _get_keep_token(session)
    if not keep_token:
        return []
    q: WeeklyLoadQuery | None = None
    if week_count is not None:
        q = WeeklyLoadQuery(week_count=week_count, date_label=f"近{week_count}周")
    async with Keep(token=keep_token) as k:
        records = await k.get_weekly_load(q)
    return [
        WeeklyLoadResponse(
            user_id=r.user_id,
            week_start=r.week_start,
            training_load=r.training_load,
            load_lower=r.load_lower,
            load_upper=r.load_upper,
        )
        for r in records
    ]
