"""数据模型定义。

使用标准库 dataclass 替代 pydantic，消除 ~1.2s 的 pydantic-core 编译开销。
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import date
from datetime import datetime
from typing import Any
from typing import Protocol
from typing import cast

from makoto.utils.tz import ensure_aware

# ── JSON 类型辅助 ──────────────────────────────────────


def _f(v: object) -> float:
    """json.loads 返回 object，转为 float。"""
    return float(v)  # type: ignore[arg-type]


def _s(v: object) -> str:
    """json.loads 返回 object，转为 str。"""
    return str(v)


def _str_list(v: object) -> list[str]:
    """json.loads 返回 object，转为 list[str]。"""
    items: list[object] = cast(list[object], v)
    return [str(x) for x in items]


def _parse_dt(v: object) -> datetime:
    """将字符串转为时区感知 datetime。"""
    if isinstance(v, str):
        return ensure_aware(datetime.fromisoformat(v))
    if isinstance(v, datetime):
        return ensure_aware(v)
    raise ValueError(f"无法解析 datetime: {v!r}")


def _parse_date(v: object) -> date:
    """将字符串转为 date。"""
    if isinstance(v, str):
        return date.fromisoformat(v)
    if isinstance(v, date):
        return v
    raise ValueError(f"无法解析 date: {v!r}")


# ── 模型协议 ────────────────────────────────────────────


class JsonlRecord(Protocol):
    """JSONL 存储所需的序列化/反序列化协议。"""

    def to_dict(self) -> dict[str, object]: ...
    @classmethod
    def from_dict(cls, d: dict[str, object]) -> Any: ...


# ── 数据模型 ────────────────────────────────────────────


@dataclass
class Food:
    """食物营养信息，以名称作为唯一标识。

    Attributes:
        name: 食物名称，唯一标识。
        calories_per_100g: 每 100 克热量（千卡）。
        protein_per_100g: 每 100 克蛋白质（克）。
        carbs_per_100g: 每 100 克碳水（克）。
        fat_per_100g: 每 100 克脂肪（克）。
        search_keywords: 搜索关键词列表。
        note: 备注。
    """

    name: str
    calories_per_100g: float = 0.0
    protein_per_100g: float = 0.0
    carbs_per_100g: float = 0.0
    fat_per_100g: float = 0.0
    search_keywords: list[str] = field(default_factory=list)
    note: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "calories_per_100g": self.calories_per_100g,
            "protein_per_100g": self.protein_per_100g,
            "carbs_per_100g": self.carbs_per_100g,
            "fat_per_100g": self.fat_per_100g,
            "search_keywords": self.search_keywords,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> Food:
        return cls(
            name=_s(d["name"]),
            calories_per_100g=_f(d.get("calories_per_100g", 0)),
            protein_per_100g=_f(d.get("protein_per_100g", 0)),
            carbs_per_100g=_f(d.get("carbs_per_100g", 0)),
            fat_per_100g=_f(d.get("fat_per_100g", 0)),
            search_keywords=_str_list(d.get("search_keywords", [])),
            note=_s(d["note"]) if d.get("note") is not None else None,
        )

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


@dataclass
class BodyLog:
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

    log_date: date
    weight_kg: float
    body_fat_pct: float
    waist_cm: float | None = None
    arm_cm: float | None = None
    thigh_cm: float | None = None
    note: str | None = None

    def to_dict(self) -> dict[str, object]:
        d: dict[str, object] = {
            "log_date": self.log_date.isoformat(),
            "weight_kg": self.weight_kg,
            "body_fat_pct": self.body_fat_pct,
        }
        if self.waist_cm is not None:
            d["waist_cm"] = self.waist_cm
        if self.arm_cm is not None:
            d["arm_cm"] = self.arm_cm
        if self.thigh_cm is not None:
            d["thigh_cm"] = self.thigh_cm
        if self.note is not None:
            d["note"] = self.note
        return d

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> BodyLog:
        return cls(
            log_date=_parse_date(d["log_date"]),
            weight_kg=_f(d["weight_kg"]),
            body_fat_pct=_f(d["body_fat_pct"]),
            waist_cm=_f(d["waist_cm"]) if d.get("waist_cm") is not None else None,
            arm_cm=_f(d["arm_cm"]) if d.get("arm_cm") is not None else None,
            thigh_cm=_f(d["thigh_cm"]) if d.get("thigh_cm") is not None else None,
            note=_s(d["note"]) if d.get("note") is not None else None,
        )


@dataclass
class DietLog:
    """饮食记录，引用食物库中已注册的食物。

    Attributes:
        log_time: 进餐日期时间。
        food_name: 引用的食物名称。
        grams: 摄入克数。
        note: 备注，选填。
    """

    log_time: datetime
    food_name: str
    grams: float
    note: str | None = None

    def to_dict(self) -> dict[str, object]:
        d: dict[str, object] = {
            "log_time": self.log_time.isoformat(),
            "food_name": self.food_name,
            "grams": self.grams,
        }
        if self.note is not None:
            d["note"] = self.note
        return d

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> DietLog:
        return cls(
            log_time=_parse_dt(d["log_time"]),
            food_name=_s(d["food_name"]),
            grams=_f(d["grams"]),
            note=_s(d["note"]) if d.get("note") is not None else None,
        )


@dataclass
class ExerciseLog:
    """运动记录。

    Attributes:
        log_time: 运动日期时间。
        exercise_name: 运动名称。
        duration_desc: 时长/组数/数量，自由文本。
        calories_kcal: 消耗热量（千卡）。
        note: 备注，选填。
    """

    log_time: datetime
    exercise_name: str
    duration_desc: str
    calories_kcal: float
    note: str | None = None

    def to_dict(self) -> dict[str, object]:
        d: dict[str, object] = {
            "log_time": self.log_time.isoformat(),
            "exercise_name": self.exercise_name,
            "duration_desc": self.duration_desc,
            "calories_kcal": self.calories_kcal,
        }
        if self.note is not None:
            d["note"] = self.note
        return d

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> ExerciseLog:
        return cls(
            log_time=_parse_dt(d["log_time"]),
            exercise_name=_s(d["exercise_name"]),
            duration_desc=_s(d["duration_desc"]),
            calories_kcal=_f(d["calories_kcal"]),
            note=_s(d["note"]) if d.get("note") is not None else None,
        )
