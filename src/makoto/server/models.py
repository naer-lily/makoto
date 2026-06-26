"""Pydantic v2 数据模型。

包含所有表对应的请求/响应模型，以及 nutricion_for 计算工具。
"""

from __future__ import annotations

from datetime import date
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel
from pydantic import Field

# ── 枚举 ──


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(StrEnum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"

    @property
    def multiplier(self) -> float:
        return {
            ActivityLevel.SEDENTARY: 1.2,
            ActivityLevel.LIGHT: 1.375,
            ActivityLevel.MODERATE: 1.55,
            ActivityLevel.ACTIVE: 1.725,
            ActivityLevel.VERY_ACTIVE: 1.9,
        }[self]


# ── 营养计算 ──


def nutrition_for(
    calories_per_100g: float,
    protein_per_100g: float,
    carbs_per_100g: float,
    fat_per_100g: float,
    grams: float,
) -> dict[str, float]:
    """计算指定克数下的营养素。

    Returns:
        {"calories_kcal": ..., "protein_g": ..., "carbs_g": ..., "fat_g": ...}
    """
    factor = grams / 100.0
    return {
        "calories_kcal": round(calories_per_100g * factor, 1),
        "protein_g": round(protein_per_100g * factor, 1),
        "carbs_g": round(carbs_per_100g * factor, 1),
        "fat_g": round(fat_per_100g * factor, 1),
    }


# ── Profile ──


class ProfileCreate(BaseModel):
    name: str
    gender: Gender
    age: int = Field(ge=1, le=120)
    height_cm: float = Field(ge=0)
    weight_kg: float = Field(ge=0)
    body_fat_pct: float = Field(ge=0, le=60)
    target_weight_kg: float = Field(ge=0)
    target_date: date
    activity_level: ActivityLevel
    keep_token: str | None = None


class ProfileResponse(ProfileCreate):
    ffm_kg: float
    bmr_kcal: float
    netee_kcal: float
    weekly_deficit_needed: float | None
    days_remaining: int


# ── Food ──


class FoodCreate(BaseModel):
    name: str
    calories_per_100g: float = Field(default=0.0, ge=0)
    protein_per_100g: float = Field(default=0.0, ge=0)
    carbs_per_100g: float = Field(default=0.0, ge=0)
    fat_per_100g: float = Field(default=0.0, ge=0)
    search_keywords: list[str] = Field(default_factory=list)
    note: str | None = None


class FoodResponse(FoodCreate):
    id: int
    created_at: str


class FoodSearchResult(BaseModel):
    id: int
    name: str
    distance: int


# ── Body Log ──


class BodyLogCreate(BaseModel):
    log_date: date
    weight_kg: float = Field(ge=0)
    body_fat_pct: float = Field(ge=0, le=60)
    note: str | None = None


class BodyLogResponse(BodyLogCreate):
    id: int
    created_at: str


# ── Circumference Log ──


class CircumferenceLogCreate(BaseModel):
    log_date: date
    waist_cm: float | None = Field(default=None, ge=0)
    arm_cm: float | None = Field(default=None, ge=0)
    thigh_cm: float | None = Field(default=None, ge=0)
    note: str | None = None


class CircumferenceLogResponse(CircumferenceLogCreate):
    id: int
    created_at: str


# ── Diet Log ──


class DietLogCreate(BaseModel):
    log_time: datetime
    food_id: int
    grams: float = Field(ge=0)
    note: str | None = None


class DietLogUpdate(BaseModel):
    log_time: datetime
    food_id: int
    grams: float = Field(ge=0)
    note: str | None = None


class DietLogResponse(DietLogCreate):
    id: int
    food_name: str
    calories_kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    food_calories_per_100g: float
    food_protein_per_100g: float
    food_carbs_per_100g: float
    food_fat_per_100g: float
    created_at: str


# ── Exercise Log ──


class ExerciseLogCreate(BaseModel):
    log_time: datetime
    exercise_name: str
    duration_desc: str
    calories_kcal: float = Field(ge=0)
    note: str | None = None


class ExerciseLogResponse(ExerciseLogCreate):
    id: int
    created_at: str


# ── Dashboard ──


class TodayBody(BaseModel):
    weight_kg: float | None = None
    body_fat_pct: float | None = None
    note: str | None = None


class TodayDietItem(BaseModel):
    log_time: str
    food_id: int
    food_name: str
    grams: float
    calories_kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float


class TodayExerciseItem(BaseModel):
    log_time: str
    exercise_name: str
    duration_desc: str
    calories_kcal: float


class TodayResponse(BaseModel):
    date: date
    body: TodayBody | None = None
    diets: list[TodayDietItem] = []
    exercises: list[TodayExerciseItem] = []
    total_intake_kcal: float = 0.0
    total_burned_kcal: float = 0.0
    total_protein_g: float = 0.0
    total_carbs_g: float = 0.0
    total_fat_g: float = 0.0
    netee_kcal: float = 0.0
    net_kcal: float = 0.0
    weight_delta_day: float | None = None
    body_fat_delta_day: float | None = None
    weight_delta_week: float | None = None
    body_fat_delta_week: float | None = None
    circumference: CircumferenceLogResponse | None = None


# Alpert 公式：每磅体脂最多分解 ~31 kcal/天 → 68.34 kcal/kg/天
# 保守取 60 kcal/kg/天（约 88% 理论极限，折合 27 kcal/lb/天）
ALPERT_KCAL_PER_KG_FAT: float = 60.0


class ReportRow(BaseModel):
    date: str
    weight_kg: float
    body_fat_pct: float
    ffm_kg: float
    fat_kg: float
    ma_weight_kg: float
    ma_body_fat_pct: float
    ma_ffm_kg: float
    ma_fat_kg: float
    deficit_kcal: float
    expected_deficit_kcal: float | None
    ma_deficit_kcal: float | None
    alpert_limit_kcal: float
    is_interpolated: bool
    weekly_loss_kg: float | None


class ReportSummary(BaseModel):
    weight_delta: float
    body_fat_delta: float
    ffm_delta: float
    ma_weight_delta: float
    ma_body_fat_delta: float
    ma_ffm_delta: float
    total_deficit_kcal: float
    total_expected_kcal: float | None
    met_target: bool | None


class ReportResponse(BaseModel):
    start_date: str
    end_date: str
    days: int
    target_weight_kg: float | None
    target_date: str | None
    rows: list[ReportRow]
    summary: ReportSummary
