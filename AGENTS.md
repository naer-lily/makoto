# makoto 项目开发约定

## 开发理念

小步快跑，增量迭代。每次只做最小的可交付单元，保持代码始终可运行。

## 语言与工具链

- **语言**: Python 3.12+
- **构建系统**: hatchling (pyproject.toml)
- **包管理器**: pip (依赖全部在 pyproject.toml 中声明，不使用 requirements.txt)
- **CLI 框架**: typer
- **数据模型**: 标准库 dataclass（已移除 pydantic，启动快 7x）
- **格式化**: black (行宽 100)
- **Lint**: ruff (严格模式)
- **类型检查**: mypy (strict)
- **测试**: pytest + pytest-cov
- **日志**: loguru

## 代码风格

### 类型标注

所有函数、方法、变量必须包含完整的类型标注。禁止使用 `Any`，除非有充分理由并在注释中说明。
使用 `X | None` 而非 `Optional[X]`（Python 3.10+ 原生语法）。

```python
def adjust_weight(current: float, delta: float) -> float | None:
    new = current + delta
    if new <= 0:
        return None
    return new
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

### 数据模型（dataclass）

所有数据结构使用标准库 `@dataclass`，每个类必须实现 `to_dict()` 和 `from_dict()` classmethod 用于 JSONL 序列化。

```python
from dataclasses import dataclass

@dataclass
class BodyMeasurement:
    weight_kg: float
    body_fat_pct: float | None = None

    def to_dict(self) -> dict[str, object]:
        return {"weight_kg": self.weight_kg, "body_fat_pct": self.body_fat_pct}

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> BodyMeasurement:
        return cls(weight_kg=float(d["weight_kg"]), body_fat_pct=...)
```

### 字符串枚举

Python 3.11+ 使用标准库 `StrEnum`：

```python
from enum import StrEnum

class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
```

### 时序工具

纯函数式设计，无副作用，可组合：

```python
from makoto.utils.timeseries import date_series, linear_interpolate, rolling_mean

dates = date_series(start, end)
filled = linear_interpolate(raw_data, dates)
smoothed = rolling_mean(filled, window=7)
```

### 输出设计

- 终端直出：rich Table + 颜色
- 管道/重定向 / `--plain`：自动 Markdown 表格，`console.py` 的 `render_table()` 统一入口
- `get_console()` 在命令函数内部调用，确保 `--plain` 或管道检测生效

### 项目结构

```
makoto/
├── src/
│   └── makoto/
│       ├── __init__.py
│       ├── main.py          # CLI 入口 + _LazyApp 延迟加载
│       ├── models/          # pydantic 数据模型
│       │   ├── records.py   # Food / BodyLog / DietLog / ExerciseLog
│       │   └── profile.py   # Gender / ActivityLevel / UserProfile
│       ├── commands/        # CLI 子命令
│       │   ├── profile.py   # 用户画像
│       │   ├── food.py      # 食物库
│       │   ├── body.py      # 身体测量
│       │   ├── diet.py      # 饮食记录
│       │   ├── exercise.py  # 运动记录
│       │   └── dashboard.py # 数据总览
│       └── utils/           # 工具函数
│           ├── jsonl_store.py   # JSONL 通用读写
│           ├── search.py        # Levenshtein 搜索
│           ├── tz.py            # 时区处理
│           ├── timeseries.py    # 时序纯函数
│           ├── console.py       # 终端输出 / Markdown 降级
│           ├── data_paths.py    # data/ 路径配置
│           └── profile_store.py # profile.json 读写
├── tests/
├── pyproject.toml
├── README.md
└── AGENTS.md
```

### 延迟加载

`main.py` 使用 `_LazyApp` 代理注册子命令，仅在用户实际调用时 import 对应模块。
避免启动时 pydantic-core 编译开销阻塞。

```python
class _LazyApp:
    def __init__(self, module_path: str, attr: str) -> None:
        self._module_path = module_path
        self._attr = attr
        self._app: Any = None

    def _load(self) -> typer.Typer:
        if self._app is None:
            mod = importlib.import_module(self._module_path)
            self._app = getattr(mod, self._attr)
        return self._app

app.add_typer(_LazyApp("makoto.commands.food", "food_app"), name="food", ...)
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
