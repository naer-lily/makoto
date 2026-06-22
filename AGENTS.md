# makoto 项目开发约定

## 开发理念

小步快跑，增量迭代。每次只做最小的可交付单元，保持代码始终可运行。

## 语言与工具链

- **语言**: Python 3.12+
- **构建系统**: hatchling (pyproject.toml)
- **包管理器**: pip (依赖全部在 pyproject.toml 中声明，不使用 requirements.txt)
- **CLI 框架**: typer
- **API 框架**: FastAPI + uvicorn
- **数据模型**: pydantic v2 (server/models.py)
- **存储**: SQLite via aiosqlite (raw sqlite3，不用 ORM)
- **HTTP 客户端**: httpx (CLI → Server 通信)
- **格式化**: black (行宽 100)
- **Lint**: ruff (严格模式)
- **类型检查**: mypy (strict)
- **测试**: pytest + pytest-cov
- **日志**: loguru

## 架构

```
makoto/                          # CLI 客户端
    --httpx--> FastAPI Server    # makoto-server 入口
                  --aiosqlite--> SQLite (data/makoto.db)
```

两个入口点：
- `makoto` — CLI 客户端（`makoto.main:app`）
- `makoto-server` — FastAPI 服务端（`makoto.server.app:main`）

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

### 数据模型（pydantic v2）

所有数据结构使用 pydantic v2 `BaseModel`，分为三类：

- `XxxCreate` — POST/PUT 入参
- `XxxResponse` — 返回体（含 id + created_at）
- 嵌套模型用于复合响应（如 Dashboard）

```python
from pydantic import BaseModel, Field

class FoodCreate(BaseModel):
    name: str
    calories_per_100g: float = Field(default=0.0, ge=0)
    protein_per_100g: float = Field(default=0.0, ge=0)
    ...

class FoodResponse(FoodCreate):
    id: int
    created_at: str
```

### 数据库操作（raw sqlite3）

不使用 ORM，直接用 aiosqlite 手动 SQL。行通过 `_dict_factory` 转为 dict：

```python
# database.py
def _dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

# routes 中
cursor = await db.execute("SELECT * FROM food WHERE id = ?", (food_id,))
row = await cursor.fetchone()
d = dict(row)
```

### 时区处理（`utils/tz.py`）

全项目统一使用 `makoto.utils.tz` 中定义的函数，**禁止**直接调 `datetime.isoformat()` 或 `date.today()` 处理时间。

**核心原则**：所有存储和传输的 datetime 字符串必须是无时区偏移的本地时间（`YYYY-MM-DDTHH:MM:SS`），因为 SQLite 的 `date()` 函数会对含时区偏移的字符串做 UTC 换算，导致日期边界错位。

**API**：

| 函数 | 返回格式 | 用途 |
|---|---|---|
| `server_tz()` | `ZoneInfo` | 服务端时区，优先 `MAKOTO_TZ` 环境变量 |
| `today_local()` | `date` | 服务端时区的"今天"，替换所有 `date.today()` |
| `ensure_aware(dt)` | `datetime` | naive → 补上服务端时区 |
| `to_store_str(dt)` | `YYYY-MM-DDTHH:MM:SS` | **存储/传输**：存 SQLite 和 HTTP 发包统一用这个 |
| `format_local(dt)` | `YYYY-MM-DD HH:MM` | **终端显示**：仅用于 CLI 用户可见输出 |

```python
# 正确：存储和传输
time_str = to_store_str(dt)

# 正确：今天的日期
today = today_local()

# 错误：会生成含时区偏移的字符串（SQLite date() 会错）
time_str = dt.isoformat()

# 错误：使用服务器本地日期而非配置时区
today = date.today()
```

**环境变量**：Docker 部署时通过 `MAKOTO_TZ=Asia/Shanghai` 指定时区。

### 鉴权

FastAPI 端点通过 `Depends(verify_token)` 保护。`verify_token` 从 `HTTPBearer` 中提取 token 与 `MAKOTO_TOKEN` 环境变量比对。CLI 客户端请求带 `Authorization: Bearer <token>` 头。

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
│       ├── main.py                # CLI 入口 + _LazyApp 延迟加载
│       ├── server/                # FastAPI 服务端
│       │   ├── __init__.py
│       │   ├── app.py             # FastAPI 应用 + lifespan + main() 入口
│       │   ├── auth.py            # Bearer token 鉴权依赖
│       │   ├── database.py        # aiosqlite 连接管理 + 建表 + dict factory
│       │   ├── models.py          # pydantic v2 全部模型 + nutrition_for()
│       │   └── routes/            # API 路由
│       │       ├── profile.py         # /api/v1/profile
│       │       ├── foods.py           # /api/v1/foods
│       │       ├── body.py            # /api/v1/body-logs
│       │       ├── circumference.py   # /api/v1/circumference-logs
│       │       ├── diet.py            # /api/v1/diet-logs
│       │       ├── exercise.py        # /api/v1/exercise-logs
│       │       └── dashboard.py       # /api/v1/dashboard/{today,report}
│       ├── client/                # HTTP 客户端
│       │   ├── __init__.py
│       │   ├── config.py          # MAKOTO_ENDPOINT / MAKOTO_TOKEN
│       │   └── api.py             # MakotoClient + get_client() 单例
│       ├── commands/              # CLI 子命令（HTTP 客户端模式）
│       │   ├── profile.py         # 用户画像
│       │   ├── food.py            # 食物库
│       │   ├── body.py            # 身体测量（体重、体脂率）
│       │   ├── circumference.py   # 围度测量（腰围、臂围、大腿围）
│       │   ├── diet.py            # 饮食记录
│       │   ├── exercise.py        # 运动记录
│       │   └── dashboard.py       # 数据总览
│       └── utils/                 # 工具函数
│           ├── console.py         # 终端输出 / Markdown 降级
│           ├── tz.py              # 时区处理
│           ├── timeseries.py      # 时序纯函数（date_series / interpolate / rolling_mean）
│           ├── search.py          # Levenshtein 模糊搜索
│           └── data_paths.py      # data/ 路径配置
├── scripts/
│   └── migrate_jsonl_to_sqlite.py # 一次性 JSONL → SQLite 迁移（不再维护）
├── data/
│   └── makoto.db                  # SQLite 数据库
├── tests/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── README.md
├── AGENTS.md
└── SKILL.md
```

### 延迟加载

`main.py` 使用 `_LazyApp` 代理注册子命令，仅在用户实际调用时 import 对应模块。

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
```

### Git 提交

- 使用中文描述，简洁明了
- 一个 commit 只做一件事
- 提交前确保 lint、typecheck、test 全部通过

## 质量门禁

**每次改动源码后，必须先补充对应的单元测试，再提交。测试文件放在 `tests/` 目录下，命名与路由模块对应。**

测试架构：
- `tests/conftest.py` — 提供 `:memory:` SQLite + `dependency_overrides` 绕过鉴权的 `TestClient` fixture
- 每个路由模块对应一个测试文件（`test_profile.py`、`test_foods.py` 等）
- 覆盖正常路径 + 异常路径（404/409/参数校验）

每次提交前执行：

```bash
ruff check src/ tests/
mypy src/
pytest -v
pytest --cov=src/makoto --cov-report=term-missing
```

在 CI 或本地均可通过 `pyproject.toml` 中配置的工具统一运行。
