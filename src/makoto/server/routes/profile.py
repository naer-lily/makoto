"""用户画像 API 路由。"""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from makoto.server.auth import verify_token
from makoto.server.database import get_session
from makoto.server.db_models import Profile
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


async def _load_profile(session: AsyncSession) -> Profile | None:
    return (
        await session.execute(select(Profile).where(Profile.id == 1))
    ).scalar_one_or_none()


def _build_response(row: Profile) -> ProfileResponse:
    target_date = date.fromisoformat(row.target_date)
    d = {
        "weight_kg": row.weight_kg,
        "height_cm": row.height_cm,
        "age": row.age,
        "body_fat_pct": row.body_fat_pct,
        "gender": row.gender,
        "activity_level": row.activity_level,
        "target_weight_kg": row.target_weight_kg,
    }
    ffm, bmr, ree, weekly, days_remaining = _compute_profile_fields(d, target_date)
    return ProfileResponse(
        name=row.name,
        gender=Gender(row.gender),
        age=row.age,
        height_cm=row.height_cm,
        weight_kg=row.weight_kg,
        body_fat_pct=row.body_fat_pct,
        target_weight_kg=row.target_weight_kg,
        target_date=target_date,
        activity_level=ActivityLevel(row.activity_level),
        keep_token=row.keep_token,
        ffm_kg=ffm,
        bmr_kcal=bmr,
        ree_kcal=ree,
        weekly_deficit_needed=weekly,
        days_remaining=days_remaining,
    )


@router.get(
    "",
    response_model=ProfileResponse,
    summary="读取用户画像",
    description="返回用户的基本信息、身体数据、活动水平、目标体重及推算出的基础代谢率与每周所需热量缺口。",
)
async def get_profile(
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> ProfileResponse:
    row = await _load_profile(session)
    if row is None:
        raise HTTPException(status_code=404, detail="用户画像未设置")
    return _build_response(row)


@router.put(
    "",
    response_model=ProfileResponse,
    summary="创建或更新用户画像",
    description="设置或覆盖用户的姓名、性别、年龄、身高、体重、体脂率、目标体重、目标日期和活动水平。",
)
async def set_profile(
    data: ProfileCreate,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> ProfileResponse:
    row = await _load_profile(session)
    if row is None:
        row = Profile(id=1, name=data.name, gender=data.gender.value, age=data.age,
                      height_cm=data.height_cm, weight_kg=data.weight_kg,
                      body_fat_pct=data.body_fat_pct,
                      target_weight_kg=data.target_weight_kg,
                      target_date=data.target_date.isoformat(),
                      activity_level=data.activity_level.value,
                      keep_token=data.keep_token)
    else:
        row.name = data.name
        row.gender = data.gender.value
        row.age = data.age
        row.height_cm = data.height_cm
        row.weight_kg = data.weight_kg
        row.body_fat_pct = data.body_fat_pct
        row.target_weight_kg = data.target_weight_kg
        row.target_date = data.target_date.isoformat()
        row.activity_level = data.activity_level.value
        row.keep_token = data.keep_token
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _build_response(row)
