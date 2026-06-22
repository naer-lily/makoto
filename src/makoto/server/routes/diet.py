"""饮食记录 API 路由。

同分钟不可重复，记录时自动计算营养素。
"""

from __future__ import annotations

import aiosqlite
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from makoto.server.auth import verify_token
from makoto.server.database import get_db
from makoto.server.models import DietLogCreate
from makoto.server.models import DietLogResponse
from makoto.server.models import DietLogUpdate
from makoto.server.models import nutrition_for
from makoto.utils.tz import to_store_str

router = APIRouter(prefix="/api/v1/diet-logs", tags=["diet"])


async def _food_base(
    db: aiosqlite.Connection, food_name: str
) -> tuple[float, float, float, float]:
    """查询食物每 100g 基准营养。

    Args:
        db: 数据库连接。
        food_name: 食物名称。

    Returns:
        (热量, 蛋白质, 碳水, 脂肪) 每 100g 基准值；食物未注册时返回全 0。
    """
    cursor = await db.execute(
        "SELECT calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g "
        "FROM food WHERE name = ?",
        (food_name,),
    )
    row = await cursor.fetchone()
    if row is None:
        return 0.0, 0.0, 0.0, 0.0
    return (
        float(row["calories_per_100g"]),
        float(row["protein_per_100g"]),
        float(row["carbs_per_100g"]),
        float(row["fat_per_100g"]),
    )


async def _row_to_response(
    db: aiosqlite.Connection, row: aiosqlite.Row
) -> DietLogResponse:
    d = dict(row)
    food_name = str(d["food_name"])
    grams = float(d["grams"])
    base_cal, base_pro, base_carb, base_fat = await _food_base(db, food_name)
    n = nutrition_for(base_cal, base_pro, base_carb, base_fat, grams)
    return DietLogResponse(
        id=int(d["id"]),
        log_time=__import__("datetime").datetime.fromisoformat(str(d["log_time"])),
        food_name=food_name,
        grams=grams,
        note=str(d["note"]) if d["note"] else None,
        calories_kcal=n["calories_kcal"],
        protein_g=n["protein_g"],
        carbs_g=n["carbs_g"],
        fat_g=n["fat_g"],
        food_calories_per_100g=base_cal,
        food_protein_per_100g=base_pro,
        food_carbs_per_100g=base_carb,
        food_fat_per_100g=base_fat,
        created_at=str(d["created_at"]),
    )


@router.get(
    "",
    response_model=list[DietLogResponse],
    summary="列出饮食记录",
    description=(
        "按时间倒序返回饮食记录，包含食物名称、克数、自动计算的营养素，"
        "以及该食物每 100g 的基准营养。支持 start/end 按日期前闭后闭过滤。"
    ),
)
async def list_diet_logs(
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
) -> list[DietLogResponse]:
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
        f"SELECT * FROM diet_log{where} ORDER BY log_time DESC LIMIT ?", params
    )
    rows = await cursor.fetchall()
    return [await _row_to_response(db, r) for r in rows]


@router.post(
    "",
    response_model=DietLogResponse,
    status_code=201,
    summary="记录一次饮食",
    description="记录一次饮食摄入（同分钟不可重复），自动根据食物库中的营养数据计算热量和营养素。",
)
async def create_diet_log(
    data: DietLogCreate,
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> DietLogResponse:
    time_str = to_store_str(data.log_time)

    # 验证食物存在
    cursor = await db.execute("SELECT id FROM food WHERE name = ?", (data.food_name,))
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail=f"食物 '{data.food_name}' 未注册")

    # 去重：同分钟不可重复
    cursor = await db.execute(
        "SELECT id FROM diet_log WHERE log_time = ?", (time_str,)
    )
    if await cursor.fetchone():
        raise HTTPException(status_code=409, detail=f"{time_str} 已有记录，请错开至少 1 分钟")

    cursor = await db.execute(
        "INSERT INTO diet_log (log_time, food_name, grams, note) VALUES (?, ?, ?, ?)",
        (time_str, data.food_name, data.grams, data.note),
    )
    await db.commit()
    log_id = cursor.lastrowid

    cursor2 = await db.execute("SELECT * FROM diet_log WHERE id = ?", (log_id,))
    row = await cursor2.fetchone()
    assert row is not None
    return await _row_to_response(db, row)


@router.put(
    "/{log_id}",
    response_model=DietLogResponse,
    summary="更新饮食记录",
    description="修改饮食记录的食物名称、克数、备注或时间。食物必须已在食物库中注册。",
)
async def update_diet_log(
    log_id: int,
    data: DietLogUpdate,
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> DietLogResponse:
    cursor = await db.execute("SELECT id FROM diet_log WHERE id = ?", (log_id,))
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="记录不存在")

    cursor2 = await db.execute("SELECT id FROM food WHERE name = ?", (data.food_name,))
    if await cursor2.fetchone() is None:
        raise HTTPException(status_code=404, detail=f"食物 '{data.food_name}' 未注册")

    time_str = to_store_str(data.log_time)
    cursor3 = await db.execute(
        "SELECT id FROM diet_log WHERE log_time = ? AND id != ?", (time_str, log_id)
    )
    if await cursor3.fetchone():
        raise HTTPException(status_code=409, detail=f"{time_str} 已有记录，请错开至少 1 分钟")

    await db.execute(
        "UPDATE diet_log SET log_time=?, food_name=?, grams=?, note=? WHERE id=?",
        (time_str, data.food_name, data.grams, data.note, log_id),
    )
    await db.commit()

    cursor4 = await db.execute("SELECT * FROM diet_log WHERE id = ?", (log_id,))
    row = await cursor4.fetchone()
    assert row is not None
    return await _row_to_response(db, row)


@router.delete(
    "/{log_id}",
    response_model=DietLogResponse,
    summary="删除饮食记录",
    description="删除指定的饮食记录，并在响应体中返回被删除记录的完整数据（含营养与食物基准）。",
)
async def delete_diet_log(
    log_id: int,
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> DietLogResponse:
    cursor = await db.execute("SELECT * FROM diet_log WHERE id = ?", (log_id,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    deleted = await _row_to_response(db, row)
    await db.execute("DELETE FROM diet_log WHERE id = ?", (log_id,))
    await db.commit()
    return deleted
