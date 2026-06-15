# makoto 项目开发约定

## 开发理念

小步快跑，增量迭代。每次只做最小的可交付单元，保持代码始终可运行。

## 语言与工具链

- **语言**: Python 3.12+
- **构建系统**: hatchling (pyproject.toml)
- **包管理器**: pip (依赖全部在 pyproject.toml 中声明，不使用 requirements.txt)
- **CLI 框架**: typer
- **数据模型**: pydantic v2
- **格式化**: black (行宽 100)
- **Lint**: ruff (严格模式)
- **类型检查**: mypy (strict)
- **测试**: pytest + pytest-cov
- **日志**: loguru

## 代码风格

### 类型标注

所有函数、方法、变量必须包含完整的类型标注。禁止使用 `Any`，除非有充分理由并在注释中说明。

```python
from typing import Optional

def calculate_bmi(weight_kg: float, height_m: float) -> float:
    return weight_kg / (height_m ** 2)
```

### 文档注释

所有公开函数、类、模块使用 Google 风格的 docstring。

```python
def get_daily_calories(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    activity_level: str,
) -> float:
    """根据 Mifflin-St Jeor 公式计算每日基础热量消耗。

    Args:
        weight_kg: 体重（公斤）
        height_cm: 身高（厘米）
        age: 年龄
        gender: 性别 ("male" | "female")
        activity_level: 活动水平 ("sedentary" | "light" | "moderate" | "active" | "very_active")

    Returns:
        每日总热量消耗估值（千卡）

    Raises:
        ValueError: 性别或活动水平取值无效
    """
    ...
```

### Pydantic 模型

所有数据结构使用 pydantic BaseModel，配置 `extra = "forbid"` 和 `validate_assignment = True`。

```python
from pydantic import BaseModel, Field, ConfigDict

class BodyMeasurement(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    weight_kg: float = Field(..., gt=0, description="体重（公斤）")
    body_fat_pct: Optional[float] = Field(None, ge=0, le=60, description="体脂率（%）")
```

### 项目结构

```
makoto/
├── src/
│   └── makoto/
│       ├── __init__.py
│       ├── main.py          # CLI 入口
│       ├── models/          # pydantic 数据模型
│       ├── commands/        # CLI 子命令
│       └── utils/           # 工具函数
├── tests/
├── pyproject.toml
└── README.md
```

### Git 提交

- 使用中文描述，简洁明了
- 一个 commit 只做一件事
- 提交前确保 lint、typecheck、test 全部通过

## 质量门禁

每次提交前执行：

```bash
ruff check src/ tests/
mypy src/
pytest -v
```

在 CI 或本地均可通过 `pyproject.toml` 中配置的工具统一运行。
