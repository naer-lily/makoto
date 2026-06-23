"""一次性迁移脚本：将 diet_log 从 food_name 软关联迁移到 food_id 外键。

自包含（仅依赖标准库），可在任意有 python3 的环境直接运行，无需安装 makoto 包：

    python3 scripts/migrate_to_food_id.py [数据库路径]

数据库路径省略时依次回退：环境变量 MAKOTO_DATA_DIR 下的 makoto.db，或 ./data/makoto.db。

执行步骤：

1. 备份原数据库。
2. 补建缺失的 circumference_log 表（幂等）。
3. 校验所有 diet_log.food_name 均能匹配 food 表（存在孤儿则中止）。
4. 重建 diet_log 表（food_name → food_id 外键 + 索引），按名称回填 food_id。
5. 标记 alembic 版本（有 alembic 则 stamp head，否则手动写入 alembic_version 表）。

幂等：若 diet_log 已是 food_id 结构则直接跳过。
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# 与 alembic/versions 下初始 revision 保持一致（initial schema with food_id fk）
INITIAL_REVISION = "f356930f4fe9"

_CIRCUMFERENCE_DDL = """
CREATE TABLE IF NOT EXISTS circumference_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    log_date    TEXT NOT NULL UNIQUE,
    waist_cm    REAL,
    arm_cm      REAL,
    thigh_cm    REAL,
    note        TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

_DIET_NEW_DDL = """
CREATE TABLE diet_log_new (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    log_time    TEXT NOT NULL,
    food_id     INTEGER NOT NULL REFERENCES food(id),
    grams       REAL NOT NULL,
    note        TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


def _resolve_db_path() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]
    data_dir = os.environ.get("MAKOTO_DATA_DIR")
    if data_dir:
        return str(Path(data_dir) / "makoto.db")
    return str(Path("data") / "makoto.db")


def _stamp_alembic(conn: sqlite3.Connection) -> None:
    """标记数据库 alembic 版本（直接写入 alembic_version 表）。

    与 ``alembic stamp head`` 等价（stamp 本质就是写该表），但零依赖、
    且始终作用于本脚本实际操作的数据库，避免依赖 env.py 的 URL 配置。
    """
    conn.execute(
        "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)"
    )
    conn.execute("DELETE FROM alembic_version")
    conn.execute(
        "INSERT INTO alembic_version (version_num) VALUES (?)", (INITIAL_REVISION,)
    )
    conn.commit()
    print(f"已标记 alembic_version = {INITIAL_REVISION}（等价 alembic stamp head）。")


def main() -> int:
    path = _resolve_db_path()
    if not Path(path).exists():
        print(f"数据库不存在：{path}")
        return 1

    conn = sqlite3.connect(path)
    cur = conn.cursor()

    cols = [r[1] for r in cur.execute("PRAGMA table_info(diet_log)")]
    if not cols:
        print("diet_log 表不存在，无需迁移。")
        conn.close()
        return 0
    if "food_id" in cols and "food_name" not in cols:
        print("diet_log 已是 food_id 结构，无需迁移。")
        conn.close()
        return 0

    backup = f"{path}.bak.{datetime.now():%Y%m%d_%H%M%S}"
    shutil.copy2(path, backup)
    print(f"已备份：{backup}")

    before = cur.execute("SELECT COUNT(*) FROM diet_log").fetchone()[0]

    orphans = [
        r[0]
        for r in cur.execute(
            "SELECT DISTINCT d.food_name FROM diet_log d "
            "WHERE NOT EXISTS (SELECT 1 FROM food f WHERE f.name = d.food_name)"
        )
    ]
    if orphans:
        print(f"发现 {len(orphans)} 个无法匹配 food 表的食物名称，中止迁移：{orphans}")
        conn.close()
        return 1

    conn.execute("PRAGMA foreign_keys=OFF")
    cur.execute(_CIRCUMFERENCE_DDL)
    cur.execute(_DIET_NEW_DDL)
    cur.execute(
        "INSERT INTO diet_log_new (id, log_time, food_id, grams, note, created_at) "
        "SELECT d.id, d.log_time, f.id, d.grams, d.note, d.created_at "
        "FROM diet_log d JOIN food f ON f.name = d.food_name"
    )
    cur.execute("DROP TABLE diet_log")
    cur.execute("ALTER TABLE diet_log_new RENAME TO diet_log")
    cur.execute("CREATE INDEX ix_diet_log_food_id ON diet_log (food_id)")

    after = cur.execute("SELECT COUNT(*) FROM diet_log").fetchone()[0]
    if before != after:
        print(f"行数不一致（迁移前 {before}，迁移后 {after}），回滚。")
        conn.rollback()
        conn.close()
        return 1

    conn.commit()
    print(f"diet_log 迁移完成：{after} 行已映射到 food_id。")

    _stamp_alembic(conn)
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
