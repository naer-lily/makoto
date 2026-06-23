# makoto

makoto（真）是一个 CLI + API 健身助手，名字来源于《偶像大师》中菊地真——那位帅气又可爱的运动系女孩。

记录身体数据、健身目标、饮食与运动日志，生成统计数据，辅助你的健身之路。

## 架构

```
makoto (CLI) --httpx--> FastAPI Server --SQLModel/async SQLAlchemy--> SQLite (data/makoto.db)
```

- **`makoto`** — CLI 客户端，通过 HTTP 调用 API
- **`makoto-server`** — FastAPI 服务端，操作 SQLite 数据，提供 REST API
- 鉴权：Bearer Token（环境变量 `MAKOTO_TOKEN`）

## 功能

| 模块 | 命令 | 说明 |
|------|------|------|
| 用户画像 | `makoto profile set/show` | 性别/身高/体重/体脂/目标/活动系数，自动计算 FFM/BMR/REE |
| 食物库 | `makoto food add/list/show/search/delete` | 注册食物（每100g营养），Levenshtein 模糊搜索 |
| 身体测量 | `makoto body log/list/delete` | 晨起体重/体脂率/围度，每日仅一条，录后自动同步画像 |
| 饮食记录 | `makoto diet log/list/delete` | 引用食物库，自动计算摄入营养，同分钟不可重复 |
| 运动记录 | `makoto exercise log/list/delete` | 运动名称/时长/消耗热量，同分钟不可重复 |
| 数据总览 | `makoto dashboard today/report` | 今日净热量、7/30日趋势报告（插值+均线），支持 `--json` 输出 |
| 服务端 | `makoto-server` | 启动 FastAPI 服务端 |

### 核心设计

- **REE 不含运动**：日常消耗 = BMR × 活动系数，运动消耗由 exercise log 独立计算。上班族即使天天运动仍选 `sedentary(×1.2)`。
- **食物先注册再引用**：饮食记录引用食物名称，自动按克数计算热量和宏观营养素。
- **唯一性约束**：身体每日一条，饮食/运动同分钟不可重复。
- **围度回溯**：今日没量围度自动取最近一次记录。
- **数据可移植**：所有数据存 `data/makoto.db`（SQLite），可整体拷贝迁移。

### 输出模式

| 场景 | 行为 |
|------|------|
| 终端直出 | rich Table + 颜色 |
| 管道/重定向 | 自动 Markdown 表格，零 ANSI 样式 |
| `--plain` | 强制 Markdown（覆盖终端模式） |

## 安装

```bash
git clone git@github.com:naer-lily/makoto.git
cd makoto
pip install -e ".[dev]"
```

## 使用

```bash
# 1. 启动服务端
MAKOTO_TOKEN=your-secret makoto-server

# 2. 配置客户端环境
export MAKOTO_TOKEN=your-secret

# 3. 设置画像（其他命令的前置条件）
makoto profile set \
  --name "真" --gender male --age 30 --height 178 --weight 78 \
  -b 21 --target-weight 72 --target-date 2026-09-15 --activity sedentary

# 注册食物
makoto food add 米饭 -c 116 -p 2.6 --carbs 25.9 -f 0.3 -k "主食,碳水"

# 记录身体数据
makoto body log -d 2026-06-15 -w 78 -b 21 --waist 80

# 记录饮食
makoto diet log -t "2026-06-15 12:30" -f 米饭 -g 300

# 记录运动
makoto exercise log -t "2026-06-15 18:00" -n 跑步 -d "5公里" -c 320

# 数据总览
makoto dashboard today
makoto dashboard report -r week
makoto dashboard report -r month --json
```

### Docker 部署

```bash
MAKOTO_TOKEN=your-secret docker-compose up -d
```

## 环境变量

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `MAKOTO_HOST` | 服务端监听地址 | `0.0.0.0` |
| `MAKOTO_PORT` | 服务端监听端口 | `8000` |
| `MAKOTO_TOKEN` | 鉴权 token（服务端+客户端共用） | 自动生成（仅服务端） |
| `MAKOTO_ENDPOINT` | CLI 客户端 API 地址 | `http://127.0.0.1:8000` |
| `MAKOTO_DATA_DIR` | 数据目录 | 项目根 `data/` |

## 开发

```bash
ruff check src/      # Lint
mypy src/            # 类型检查
pytest -v            # 测试
```
