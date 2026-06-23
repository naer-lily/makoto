"""Keep 运动数据代理路由。

从用户画像中的 keep_token 读取 Keep API 凭证，
代理请求体能水平、周运动负荷等图表数据。
返回干净字段名（无 Keep 内部 $ 别名）。
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from makoto.server.auth import verify_token
from makoto.server.database import get_session
from makoto.server.db_models import Profile
from makoto.server.keep_client import Keep

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
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> list[FitnessResponse]:
    keep_token = await _get_keep_token(session)
    if not keep_token:
        return []
    async with Keep(token=keep_token) as k:
        records = await k.get_fitness()
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
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> list[WeeklyLoadResponse]:
    keep_token = await _get_keep_token(session)
    if not keep_token:
        return []
    async with Keep(token=keep_token) as k:
        records = await k.get_weekly_load()
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
