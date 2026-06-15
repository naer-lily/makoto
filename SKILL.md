---
name: makoto
description: CLI + API 健身助手。记录身体数据、饮食与运动，生成统计数据。通过 FastAPI 服务端操作 SQLite 数据库，CLI 通过 HTTP 调用。
---

# makoto — CLI + API 健身助手

makoto 是一个健身追踪工具，名字来源于《偶像大师》中菊地真——那位帅气又可爱的运动系女孩。

## 架构

```
makoto (CLI) --httpx--> FastAPI Server --aiosqlite--> SQLite (data/makoto.db)
```

- `makoto` — CLI 客户端，通过 HTTP 调用 API
- `makoto-server` — FastAPI 服务端，操作 SQLite 数据库，提供 REST API
- 鉴权：Bearer Token（环境变量 `MAKOTO_TOKEN`）

## 安装

```bash
pip install makoto
```

## 环境配置

使用前需配置以下环境变量指向已运行的服务端：

```bash
export MAKOTO_ENDPOINT=http://127.0.0.1:8000
export MAKOTO_TOKEN=your-secret-token
```

## 快速上手

1. **启动服务端** — `makoto-server`
2. **设定画像** — 录入性别、身高、体重、目标
3. **录入食物库** — 把常吃的食物及其营养数据加进去
4. **每日记录** — 晨起体重、三餐饮食、运动消耗
5. **查看总览** — 今日净热量、7 日/30 日趋势报告

第一步：设定你的个人画像。

```bash
makoto profile set --name "张三" --gender male --age 30 --height 175 -w 80 -b 18 --target-weight 72 --target-date 2026-09-15 -a moderate
```

- `--gender`: `male` | `female`
- `-a` / `--activity`: `sedentary` | `light` | `moderate` | `active` | `very_active`
- `-b` / `--body-fat`: 体脂率（%）
- `--target-date`: 目标达成日期，格式 `YYYY-MM-DD`

系统会根据画像自动计算 FFM（去脂体重）、BMR（基础代谢）和 REE（每日消耗估算），并在 dashboard 中使用。

## 食物库

录入常吃食物，之后记饮食时直接引用，自动按克数换算。

```bash
# 添加食物（每 100g 的营养值）
makoto food add 鸡蛋 -c 155 -p 13 --carbs 1.1 -f 11 -k "水煮蛋,煎蛋"

# 列出所有食物
makoto food list

# 查看某食物详情
makoto food show 鸡蛋

# 模糊搜索
makoto food search 鸡胸 -n 10

# 删除
makoto food delete 鸡蛋
```

- `-c` / `--calories`: 每 100g 热量（千卡）
- `-p` / `--protein`: 蛋白质（克）
- `--carbs`: 碳水（克）
- `-f` / `--fat`: 脂肪（克）
- `-k` / `--keywords`: 搜索关键词（逗号分隔），方便模糊搜索命中
- `-n` / `--note`: 备注
- `search` 的 `-n` / `--limit` 控制返回条数，默认 20

## 身体测量

每天早上记录体重和体脂率，可选记录腰围、臂围、腿围。每个日期仅一条记录。

```bash
# 记录今日
makoto body log -w 80.5 -b 17.8 --waist 82 --arm 35 --thigh 58 -n "晨起空腹"

# 补录某天（日期格式 YYYY-MM-DD）
makoto body log -d 2026-06-10 -w 81.2 -b 18.1

# 列表
makoto body list

# 删除某天记录
makoto body delete -d 2026-06-10
```

- `-w` / `--weight`: 体重（公斤）
- `-b` / `--body-fat`: 体脂率（%）
- `--waist`, `--arm`, `--thigh`: 围度（厘米）
- `-n` / `--note`: 备注

录入后画像中的体重和体脂率自动同步。

## 饮食记录

引用食物库中的食物，按实际克数自动计算摄入营养。

```bash
# 记录一餐
makoto diet log -t "2026-06-15 08:00" -f 鸡蛋 -g 200 -n "早餐"

# 列表（最近 N 条，默认 50）
makoto diet list -n 20

# 删除（按精确时间）
makoto diet delete -t "2026-06-15 08:00"
```

- `-t` / `--time`: 进食时间，支持 `YYYY-MM-DD HH:MM`
- `-f` / `--food`: 食物名称（必须在食物库中存在）
- `-g` / `--grams`: 食用克数

同分钟不可重复。

## 运动记录

```bash
# 记录运动
makoto exercise log -t "2026-06-15 18:30" -n 跑步 -d "5 公里, 30 分钟" -c 350 --note "户外"

# 列表
makoto exercise list -n 10

# 删除
makoto exercise delete -t "2026-06-15 18:30"
```

- `-t` / `--time`: 运动时间
- `-n` / `--name`: 运动名称
- `-d` / `--duration`: 时长描述（自由文本）
- `-c` / `--calories`: 消耗热量（千卡）

同分钟不可重复。

## Dashboard 总览

```bash
# 今日概览：净热量（摄入 - 消耗）、体重变化
makoto dashboard today

# 7 日或 30 日趋势报告（插值 + 7 日均线平滑）
makoto dashboard report -r week
makoto dashboard report -r month

# JSON 格式输出（供程序消费）
makoto dashboard report -r week --json
```

## 全局选项

```bash
# 管道/重定向友好输出（禁用颜色和富文本，转为 Markdown 表格）
makoto food list --plain
```

## 环境变量

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `MAKOTO_ENDPOINT` | API 地址 | `http://127.0.0.1:8000` |
| `MAKOTO_TOKEN` | 鉴权 token | 空 |
