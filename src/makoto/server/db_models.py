"""SQLModel 表模型（数据库层）。

与 ``models.py`` 中的 Pydantic API 模型分离，仅描述持久化结构。

设计约定：

- 所有 datetime/date 字段一律以 ``str``（TEXT）存储，写入格式由
  ``utils.tz.to_store_str`` / ``date.isoformat()`` 统一控制，
  以兼容 SQLite ``date()`` 的日期边界查询，避免原生 DateTime 类型改变存储语义。
- ``created_at`` 由数据库 ``datetime('now')`` 生成（UTC），与原始 DDL 行为一致。
- ``search_keywords`` 保留为 JSON 字符串（TEXT），读写沿用 json.dumps/loads。
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlmodel import CheckConstraint
from sqlmodel import Field
from sqlmodel import SQLModel

_CREATED_AT = sa.text("(datetime('now'))")


class Profile(SQLModel, table=True):
    """用户画像（单例，id 固定为 1）。"""

    __tablename__ = "profile"
    __table_args__ = (CheckConstraint("id = 1", name="profile_singleton"),)

    id: int | None = Field(default=None, primary_key=True)
    name: str
    gender: str
    age: int
    height_cm: float
    weight_kg: float
    body_fat_pct: float
    target_weight_kg: float
    target_date: str
    activity_level: str
    keep_token: str | None = Field(default=None)


class Food(SQLModel, table=True):
    """食物库条目（每 100g 基准营养）。"""

    __tablename__ = "food"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(sa_column=sa.Column(sa.Text, nullable=False, unique=True))
    calories_per_100g: float = Field(default=0.0)
    protein_per_100g: float = Field(default=0.0)
    carbs_per_100g: float = Field(default=0.0)
    fat_per_100g: float = Field(default=0.0)
    search_keywords: str = Field(default="[]")
    note: str | None = Field(default=None)
    created_at: str | None = Field(
        default=None,
        sa_column=sa.Column(sa.Text, nullable=False, server_default=_CREATED_AT),
    )


class BodyLog(SQLModel, table=True):
    """身体测量记录（每日一条）。"""

    __tablename__ = "body_log"

    id: int | None = Field(default=None, primary_key=True)
    log_date: str = Field(sa_column=sa.Column(sa.Text, nullable=False, unique=True))
    weight_kg: float
    body_fat_pct: float
    note: str | None = Field(default=None)
    created_at: str | None = Field(
        default=None,
        sa_column=sa.Column(sa.Text, nullable=False, server_default=_CREATED_AT),
    )


class CircumferenceLog(SQLModel, table=True):
    """围度测量记录（每日一条，三围可选）。"""

    __tablename__ = "circumference_log"

    id: int | None = Field(default=None, primary_key=True)
    log_date: str = Field(sa_column=sa.Column(sa.Text, nullable=False, unique=True))
    waist_cm: float | None = Field(default=None)
    arm_cm: float | None = Field(default=None)
    thigh_cm: float | None = Field(default=None)
    note: str | None = Field(default=None)
    created_at: str | None = Field(
        default=None,
        sa_column=sa.Column(sa.Text, nullable=False, server_default=_CREATED_AT),
    )


class DietLog(SQLModel, table=True):
    """饮食记录（通过 food_id 外键关联 food 表）。"""

    __tablename__ = "diet_log"

    id: int | None = Field(default=None, primary_key=True)
    log_time: str
    food_id: int = Field(foreign_key="food.id", index=True)
    grams: float
    note: str | None = Field(default=None)
    created_at: str | None = Field(
        default=None,
        sa_column=sa.Column(sa.Text, nullable=False, server_default=_CREATED_AT),
    )


class ExerciseLog(SQLModel, table=True):
    """运动记录。"""

    __tablename__ = "exercise_log"

    id: int | None = Field(default=None, primary_key=True)
    log_time: str
    exercise_name: str
    duration_desc: str
    calories_kcal: float
    note: str | None = Field(default=None)
    created_at: str | None = Field(
        default=None,
        sa_column=sa.Column(sa.Text, nullable=False, server_default=_CREATED_AT),
    )
