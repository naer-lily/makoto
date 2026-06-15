"""数据模型定义。

所有模型使用 pydantic v2，配置 extra="forbid" 与 validate_assignment=True。
DateTime 字段自动补全本地时区。
"""

from datetime import date
from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from makoto.utils.tz import ensure_aware


class Food(BaseModel):
    """食物营养信息，以名称作为唯一标识。

    Attributes:
        name: 食物名称，唯一标识。
        calories_per_100g: 每 100 克热量（千卡）。
        protein_per_100g: 每 100 克蛋白质（克）。
        carbs_per_100g: 每 100 克碳水（克）。
        fat_per_100g: 每 100 克脂肪（克）。
        search_keywords: 搜索关键词列表，与名称共同参与搜索。
        note: 备注。
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    name: str = Field(..., min_length=1, description="食物名称")
    calories_per_100g: float = Field(..., ge=0, description="每 100 克热量（千卡）")
    protein_per_100g: float = Field(..., ge=0, description="每 100 克蛋白质（克）")
    carbs_per_100g: float = Field(..., ge=0, description="每 100 克碳水（克）")
    fat_per_100g: float = Field(..., ge=0, description="每 100 克脂肪（克）")
    search_keywords: list[str] = Field(default_factory=list, description="搜索关键词")
    note: str | None = Field(None, description="备注")

    def nutrition_for(self, grams: float) -> dict[str, float]:
        """计算指定克数的营养摄入。

        Args:
            grams: 摄入克数。

        Returns:
            包含 calories_kcal、protein_g、carbs_g、fat_g 的字典。
        """
        factor = grams / 100.0
        return {
            "calories_kcal": round(self.calories_per_100g * factor, 1),
            "protein_g": round(self.protein_per_100g * factor, 1),
            "carbs_g": round(self.carbs_per_100g * factor, 1),
            "fat_g": round(self.fat_per_100g * factor, 1),
        }


class BodyLog(BaseModel):
    """身体测量记录，假设晨起空腹测量。

    Attributes:
        log_date: 测量日期。
        weight_kg: 体重（公斤）。
        body_fat_pct: 体脂率（%）。
        waist_cm: 腰围（厘米），选填。
        arm_cm: 臂围（厘米），选填。
        thigh_cm: 大腿围（厘米），选填。
        note: 备注，选填。
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    log_date: date = Field(..., description="测量日期")
    weight_kg: float = Field(..., gt=0, description="体重（公斤）")
    body_fat_pct: float = Field(..., ge=0, le=60, description="体脂率（%）")
    waist_cm: float | None = Field(None, gt=0, description="腰围（厘米）")
    arm_cm: float | None = Field(None, gt=0, description="臂围（厘米）")
    thigh_cm: float | None = Field(None, gt=0, description="大腿围（厘米）")
    note: str | None = Field(None, description="备注")


class DietLog(BaseModel):
    """饮食记录，引用食物库中已注册的食物。

    Attributes:
        log_time: 进餐日期时间，自动补全为本地时区。
        food_name: 引用的食物名称，必须已在食物库中注册。
        grams: 摄入克数。
        note: 备注，选填。
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    log_time: datetime = Field(..., description="进餐日期时间")
    food_name: str = Field(..., min_length=1, description="食物名称（引用食物库）")
    grams: float = Field(..., gt=0, description="摄入克数")
    note: str | None = Field(None, description="备注")

    @field_validator("log_time", mode="before")
    @classmethod
    def _ensure_aware(cls, v: Any) -> datetime:
        """将 log_time 转为时区感知的 datetime。"""
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        if isinstance(v, datetime):
            return ensure_aware(v)
        raise ValueError(f"无法解析 log_time: {v!r}")


class ExerciseLog(BaseModel):
    """运动记录。

    Attributes:
        log_time: 运动日期时间，自动补全为本地时区。
        exercise_name: 运动名称。
        duration_desc: 时长/组数/数量，自由文本。
        calories_kcal: 消耗热量（千卡）。
        note: 备注，选填。
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    log_time: datetime = Field(..., description="运动日期时间")
    exercise_name: str = Field(..., min_length=1, description="运动名称")
    duration_desc: str = Field(..., min_length=1, description="时长/组数/数量")
    calories_kcal: float = Field(..., ge=0, description="消耗热量（千卡）")
    note: str | None = Field(None, description="备注")

    @field_validator("log_time", mode="before")
    @classmethod
    def _ensure_aware(cls, v: Any) -> datetime:
        """将 log_time 转为时区感知的 datetime。"""
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        if isinstance(v, datetime):
            return ensure_aware(v)
        raise ValueError(f"无法解析 log_time: {v!r}")
