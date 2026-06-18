"""身体测量 API 路由。

每个日期仅允许一条记录，录入后自动同步画像。
"""

from __future__ import annotations

import aiosqlite
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from makoto.server.auth import verify_token
from makoto.server.database import get_db
from makoto.server.models import BodyLogCreate
from makoto.server.models import BodyLogResponse

router = APIRouter(prefix="/api/v1/body-logs", tags=["body"])


def _row_to_response(row: aiosqlite.Row) -> BodyLogResponse:
    d = dict(row)
    return BodyLogResponse(
        id=int(d["id"]),
        log_date=__import__("datetime").date.fromisoformat(str(d["log_date"])),
        weight_kg=float(d["weight_kg"]),
        body_fat_pct=float(d["body_fat_pct"]),
        note=str(d["note"]) if d["note"] else None,
        created_at=str(d["created_at"]),
    )


@router.get(
    "",
    response_model=list[BodyLogResponse],
    summary="列出身体测量记录",
    description="按日期倒序返回所有身体测量记录，包含体重、体脂率。",
)
async def list_body_logs(
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[BodyLogResponse]:
    cursor = await db.execute("SELECT * FROM body_log ORDER BY log_date DESC")
    rows = await cursor.fetchall()
    return [_row_to_response(r) for r in rows]


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
    db: aiosqlite.Connection = Depends(get_db),
) -> BodyLogResponse:
    date_str = data.log_date.isoformat()
    cursor = await db.execute("SELECT id FROM body_log WHERE log_date = ?", (date_str,))
    if await cursor.fetchone():
        raise HTTPException(status_code=409, detail=f"{date_str} 已有记录")

    cursor = await db.execute(
        "INSERT INTO body_log (log_date, weight_kg, body_fat_pct, note) VALUES (?, ?, ?, ?)",
        (date_str, data.weight_kg, data.body_fat_pct, data.note),
    )
    await db.commit()
    log_id = cursor.lastrowid

    await db.execute(
        "UPDATE profile SET weight_kg = ?, body_fat_pct = ? WHERE id = 1",
        (data.weight_kg, data.body_fat_pct),
    )
    await db.commit()

    cursor2 = await db.execute("SELECT * FROM body_log WHERE id = ?", (log_id,))
    row = await cursor2.fetchone()
    assert row is not None
    return _row_to_response(row)


@router.delete(
    "/{log_id}",
    summary="删除身体测量记录",
    description="删除指定的身体测量记录。",
)
async def delete_body_log(
    log_id: int,
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, str]:
    cursor = await db.execute("SELECT id FROM body_log WHERE id = ?", (log_id,))
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    await db.execute("DELETE FROM body_log WHERE id = ?", (log_id,))
    await db.commit()
    return {"detail": "已删除"}
