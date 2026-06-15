"""用户画像数据模型。

性别、活动系数使用 StrEnum（Python 3.11+）。
计算属性 FFM/BMR/REE 仅通过 property 暴露，不参与序列化。
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class Gender(StrEnum):
    """性别，影响 BMR 公式。"""

    MALE = "male"
    FEMALE = "female"


class ActivityLevel(StrEnum):
    """日常活动系数——不含刻意运动（运动热量由 exercise log 单独计算）。

    即使每周去 5 次健身房，办公室工作者仍应选 sedentary。
    """

    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"

    @property
    def multiplier(self) -> float:
        """返回活动系数倍率。"""
        return {
            self.SEDENTARY: 1.2,
            self.LIGHT: 1.375,
            self.MODERATE: 1.55,
            self.ACTIVE: 1.725,
            self.VERY_ACTIVE: 1.9,
        }[self]


class UserProfile(BaseModel):
    """用户画像，持有一份个人基本数据与目标。

    Attributes:
        name: 姓名（暂未使用）。
        gender: 性别，影响 BMR。
        age: 年龄。
        height_cm: 身高（厘米）。
        weight_kg: 当前体重（公斤）。
        body_fat_pct: 体脂率（%）。
        target_weight_kg: 目标体重（公斤）。
        target_date: 目标达成日期。
        activity_level: 日常活动系数（不含刻意运动）。
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    name: str = Field(..., min_length=1, description="姓名")
    gender: Gender = Field(..., description="性别")
    age: int = Field(..., ge=1, le=120, description="年龄")
    height_cm: float = Field(..., gt=0, description="身高（厘米）")
    weight_kg: float = Field(..., gt=0, description="当前体重（公斤）")
    body_fat_pct: float = Field(..., ge=0, le=60, description="体脂率（%）")
    target_weight_kg: float = Field(..., gt=0, description="目标体重（公斤）")
    target_date: date = Field(..., description="目标达成日期")
    activity_level: ActivityLevel = Field(..., description="日常活动系数")

    @property
    def ffm_kg(self) -> float:
        """去脂体重（Fat-Free Mass）。

        计算公式: weight × (1 - body_fat_pct / 100)
        """
        return round(self.weight_kg * (1 - self.body_fat_pct / 100), 1)

    @property
    def bmr_kcal(self) -> float:
        """基础代谢率（Basal Metabolic Rate）。

        使用 Mifflin-St Jeor 公式:
            male:   10 × weight + 6.25 × height - 5 × age + 5
            female: 10 × weight + 6.25 × height - 5 × age - 161
        """
        base = (
            10 * self.weight_kg
            + 6.25 * self.height_cm
            - 5 * self.age
        )
        if self.gender == Gender.MALE:
            return round(base + 5, 1)
        return round(base - 161, 1)

    @property
    def ree_kcal(self) -> float:
        """每日基础消耗（Resting Energy Expenditure）。

        计算公式: BMR × activity_multiplier，不含刻意运动。
        """
        return round(self.bmr_kcal * self.activity_level.multiplier, 1)

    @property
    def weekly_deficit_needed(self) -> float | None:
        """距离目标日期的每周热量缺口需求（千卡）。

        Returns:
            每周需消耗的热量缺口，若目标日期已过返回 None。
        """
        remaining_days = (self.target_date - date.today()).days
        if remaining_days <= 0:
            return None
        kg_to_lose = self.weight_kg - self.target_weight_kg
        total_deficit = kg_to_lose * 7700  # 1 kg ≈ 7700 kcal
        return round(total_deficit / (remaining_days / 7), 1)
