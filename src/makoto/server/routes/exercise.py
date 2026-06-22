"""运动记录 API 路由。

同分钟不可重复。
"""

from __future__ import annotations

import aiosqlite
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from makoto.server.auth import verify_token
from makoto.server.database import get_db
from makoto.server.models import ExerciseLogCreate
from makoto.server.models import ExerciseLogResponse
from makoto.utils.tz import to_store_str

router = APIRouter(prefix="/api/v1/exercise-logs", tags=["exercise"])


def _row_to_response(row: aiosqlite.Row) -> ExerciseLogResponse:
    d = dict(row)
    return ExerciseLogResponse(
        id=int(d["id"]),
        log_time=__import__("datetime").datetime.fromisoformat(str(d["log_time"])),
        exercise_name=str(d["exercise_name"]),
        duration_desc=str(d["duration_desc"]),
        calories_kcal=float(d["calories_kcal"]),
        note=str(d["note"]) if d["note"] else None,
        created_at=str(d["created_at"]),
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
    db: aiosqlite.Connection = Depends(get_db),
) -> list[ExerciseLogResponse]:
    clauses: list[str] = []
    params: list[object] = []
    if start is not None:
        clauses.append("date(log_time) >= date(?)")
        params.append(start)
    if end is not None:
        clauses.append("date(log_time) <= date(?)")
        params.append(end)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(limit)
    cursor = await db.execute(
        f"SELECT * FROM exercise_log{where} ORDER BY log_time DESC LIMIT ?", params
    )
    rows = await cursor.fetchall()
    return [_row_to_response(r) for r in rows]


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
    db: aiosqlite.Connection = Depends(get_db),
) -> ExerciseLogResponse:
    time_str = to_store_str(data.log_time)

    cursor = await db.execute(
        "SELECT id FROM exercise_log WHERE log_time = ?", (time_str,)
    )
    if await cursor.fetchone():
        raise HTTPException(status_code=409, detail=f"{time_str} 已有记录，请错开至少 1 分钟")

    cursor = await db.execute(
        """INSERT INTO exercise_log (log_time, exercise_name, duration_desc, calories_kcal, note)
           VALUES (?, ?, ?, ?, ?)""",
        (time_str, data.exercise_name, data.duration_desc, data.calories_kcal, data.note),
    )
    await db.commit()
    log_id = cursor.lastrowid

    cursor2 = await db.execute("SELECT * FROM exercise_log WHERE id = ?", (log_id,))
    row = await cursor2.fetchone()
    assert row is not None
    return _row_to_response(row)


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
    db: aiosqlite.Connection = Depends(get_db),
) -> ExerciseLogResponse:
    cursor = await db.execute("SELECT id FROM exercise_log WHERE id = ?", (log_id,))
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="记录不存在")

    time_str = to_store_str(data.log_time)
    cursor2 = await db.execute(
        "SELECT id FROM exercise_log WHERE log_time = ? AND id != ?", (time_str, log_id)
    )
    if await cursor2.fetchone():
        raise HTTPException(status_code=409, detail=f"{time_str} 已有记录，请错开至少 1 分钟")

    await db.execute(
        """UPDATE exercise_log
           SET log_time=?, exercise_name=?, duration_desc=?, calories_kcal=?, note=?
           WHERE id=?""",
        (time_str, data.exercise_name, data.duration_desc, data.calories_kcal, data.note, log_id),
    )
    await db.commit()

    cursor3 = await db.execute("SELECT * FROM exercise_log WHERE id = ?", (log_id,))
    row = await cursor3.fetchone()
    assert row is not None
    return _row_to_response(row)


@router.delete(
    "/{log_id}",
    response_model=ExerciseLogResponse,
    summary="删除运动记录",
    description="删除指定的运动记录，并在响应体中返回被删除记录的完整数据。",
)
async def delete_exercise_log(
    log_id: int,
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> ExerciseLogResponse:
    cursor = await db.execute("SELECT * FROM exercise_log WHERE id = ?", (log_id,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    deleted = _row_to_response(row)
    await db.execute("DELETE FROM exercise_log WHERE id = ?", (log_id,))
    await db.commit()
    return deleted
