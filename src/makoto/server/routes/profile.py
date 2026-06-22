"""用户画像 API 路由。"""

from __future__ import annotations

from datetime import date
from typing import Any

import aiosqlite
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from makoto.server.auth import verify_token
from makoto.server.database import get_db
from makoto.server.models import ActivityLevel
from makoto.server.models import Gender
from makoto.server.models import ProfileCreate
from makoto.server.models import ProfileResponse
from makoto.utils.tz import today_local

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


def _bmr(weight: float, height: float, age: int, gender: Gender) -> float:
    base = 10 * weight + 6.25 * height - 5 * age
    return round(base + 5 if gender == Gender.MALE else base - 161, 1)


def _compute_profile_fields(
    d: dict[str, Any], target_date: date
) -> tuple[float, float, float, float | None, int]:
    weight = float(d["weight_kg"])
    height = float(d["height_cm"])
    age = int(d["age"])
    bf = float(d["body_fat_pct"])
    gender = Gender(str(d["gender"]))
    activity = ActivityLevel(str(d["activity_level"]))
    target = float(d["target_weight_kg"])

    ffm = round(weight * (1 - bf / 100), 1)
    bmr = _bmr(weight, height, age, gender)
    ree = round(bmr * activity.multiplier, 1)
    days = (target_date - today_local()).days
    weekly = None
    if days > 0:
        weekly = round((weight - target) * 7700 / (max(days / 7, 1)), 1)
    return ffm, bmr, ree, weekly, days


@router.get(
    "",
    response_model=ProfileResponse,
    summary="读取用户画像",
    description="返回用户的基本信息、身体数据、活动水平、目标体重及推算出的基础代谢率与每周所需热量缺口。",
)
async def get_profile(
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> ProfileResponse:
    cursor = await db.execute("SELECT * FROM profile WHERE id = 1")
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="用户画像未设置")
    d = dict(row)
    target_date = date.fromisoformat(str(d["target_date"]))
    ffm, bmr, ree, weekly, days_remaining = _compute_profile_fields(d, target_date)
    return ProfileResponse(
        name=str(d["name"]),
        gender=Gender(str(d["gender"])),
        age=int(d["age"]),
        height_cm=float(d["height_cm"]),
        weight_kg=float(d["weight_kg"]),
        body_fat_pct=float(d["body_fat_pct"]),
        target_weight_kg=float(d["target_weight_kg"]),
        target_date=target_date,
        activity_level=ActivityLevel(str(d["activity_level"])),
        keep_token=str(d["keep_token"]) if d.get("keep_token") else None,
        ffm_kg=ffm,
        bmr_kcal=bmr,
        ree_kcal=ree,
        weekly_deficit_needed=weekly,
        days_remaining=days_remaining,
    )


@router.put(
    "",
    response_model=ProfileResponse,
    summary="创建或更新用户画像",
    description="设置或覆盖用户的姓名、性别、年龄、身高、体重、体脂率、目标体重、目标日期和活动水平。",
)
async def set_profile(
    data: ProfileCreate,
    _token: str = Depends(verify_token),
    db: aiosqlite.Connection = Depends(get_db),
) -> ProfileResponse:
    await db.execute(
        """INSERT OR REPLACE INTO profile
           (id, name, gender, age, height_cm, weight_kg, body_fat_pct,
            target_weight_kg, target_date, activity_level, keep_token)
           VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data.name,
            data.gender.value,
            data.age,
            data.height_cm,
            data.weight_kg,
            data.body_fat_pct,
            data.target_weight_kg,
            data.target_date.isoformat(),
            data.activity_level.value,
            data.keep_token,
        ),
    )
    await db.commit()
    d = {
        "name": data.name,
        "gender": data.gender.value,
        "age": data.age,
        "height_cm": data.height_cm,
        "weight_kg": data.weight_kg,
        "body_fat_pct": data.body_fat_pct,
        "target_weight_kg": data.target_weight_kg,
        "activity_level": data.activity_level.value,
    }
    ffm, bmr, ree, weekly, days_remaining = _compute_profile_fields(d, data.target_date)
    return ProfileResponse(
        name=data.name,
        gender=data.gender,
        age=data.age,
        height_cm=data.height_cm,
        weight_kg=data.weight_kg,
        body_fat_pct=data.body_fat_pct,
        target_weight_kg=data.target_weight_kg,
        target_date=data.target_date,
        activity_level=data.activity_level,
        keep_token=data.keep_token,
        ffm_kg=ffm,
        bmr_kcal=bmr,
        ree_kcal=ree,
        weekly_deficit_needed=weekly,
        days_remaining=days_remaining,
    )
