"""围度测量 API 路由。

每个日期仅允许一条记录，三围均为可选字段。
"""

from __future__ import annotations

from datetime import date

import aiosqlite
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from makoto.server.auth import verify_token
from makoto.server.database import get_db
from makoto.server.models import CircumferenceLogCreate
from makoto.server.models import CircumferenceLogResponse

router = APIRouter(prefix="/api/v1/circumference-logs", tags=["circumference"])


def _row_to_response(row: aiosqlite.Row) -> CircumferenceLogResponse:
    d = dict(row)
    return CircumferenceLogResponse(
        id=int(d["id"]),
        log_date=date.fromisoformat(str(d["log_date"])),
        waist_cm=float(d["waist_cm"]) if d["waist_cm"] is not None else None,
        arm_cm=float(d["arm_cm"]) if d["arm_cm"] is not None else None,
        thigh_cm=float(d["thigh_cm"]) if d["thigh_cm"] is not None else None,
        note=str(d["note"]) if d["note"] else None,
        created_at=str(d["created_at"]),
    )


@router.get(
    "",
    response_model=list[CircumferenceLogResponse],
    summary="列出围度测量记录",
    description="按日期倒序返回所有围度测量记录。",
)
async def list_circumference_logs(
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[CircumferenceLogResponse]:
    cursor = await db.execute("SELECT * FROM circumference_log ORDER BY log_date DESC")
    rows = await cursor.fetchall()
    return [_row_to_response(r) for r in rows]


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
    db: aiosqlite.Connection = Depends(get_db),
) -> CircumferenceLogResponse:
    date_str = data.log_date.isoformat()
    cursor = await db.execute(
        "SELECT id FROM circumference_log WHERE log_date = ?", (date_str,)
    )
    if await cursor.fetchone():
        raise HTTPException(status_code=409, detail=f"{date_str} 已有围度记录")

    cursor = await db.execute(
        "INSERT INTO circumference_log (log_date, waist_cm, arm_cm, thigh_cm, note) "
        "VALUES (?, ?, ?, ?, ?)",
        (date_str, data.waist_cm, data.arm_cm, data.thigh_cm, data.note),
    )
    await db.commit()
    log_id = cursor.lastrowid

    cursor2 = await db.execute("SELECT * FROM circumference_log WHERE id = ?", (log_id,))
    row = await cursor2.fetchone()
    assert row is not None
    return _row_to_response(row)


@router.delete(
    "/{log_id}",
    summary="删除围度测量记录",
    description="删除指定的围度测量记录。",
)
async def delete_circumference_log(
    log_id: int,
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, str]:
    cursor = await db.execute("SELECT id FROM circumference_log WHERE id = ?", (log_id,))
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    await db.execute("DELETE FROM circumference_log WHERE id = ?", (log_id,))
    await db.commit()
    return {"detail": "已删除"}
