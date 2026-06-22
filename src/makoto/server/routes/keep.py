"""Keep 运动数据代理路由。

从用户画像中的 keep_token 读取 Keep API 凭证，
代理请求体能水平、周运动负荷等图表数据。
返回干净字段名（无 Keep 内部 $ 别名）。
"""

from __future__ import annotations

import aiosqlite
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel

from makoto.server.auth import verify_token
from makoto.server.database import get_db
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


async def _get_keep_token(db: aiosqlite.Connection) -> str | None:
    cursor = await db.execute("SELECT keep_token FROM profile WHERE id = 1")
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="用户画像未设置")
    d = dict(row)
    return str(d["keep_token"]) if d.get("keep_token") else None


@router.get(
    "/fitness",
    response_model=list[FitnessResponse],
    summary="体能水平 (ATL/CTL/TSB)",
)
async def get_fitness(
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[FitnessResponse]:
    keep_token = await _get_keep_token(db)
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
    db: aiosqlite.Connection = Depends(get_db),
) -> list[WeeklyLoadResponse]:
    keep_token = await _get_keep_token(db)
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
