"""SQLite 数据库连接管理。

使用 aiosqlite 异步桥接 raw sqlite3，通过 FastAPI lifespan 管理生命周期。
"""

from __future__ import annotations

import aiosqlite

_db_path: str = ""
_conn: aiosqlite.Connection | None = None


def _dict_factory(
    cursor: aiosqlite.Cursor, row: tuple[object, ...]
) -> dict[str, object]:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def set_db_path(path: str) -> None:
    """设置数据库文件路径（在应用启动时调用）。"""
    global _db_path
    _db_path = path


async def connect() -> aiosqlite.Connection:
    """创建并缓存数据库连接（由 lifespan 调用）。"""
    global _conn
    _conn = await aiosqlite.connect(_db_path)
    _conn.row_factory = _dict_factory  # type: ignore[assignment]
    return _conn


async def disconnect() -> None:
    """关闭数据库连接。"""
    global _conn
    if _conn:
        await _conn.close()
        _conn = None


async def get_db() -> aiosqlite.Connection:
    """获取数据库连接（FastAPI 依赖注入用）。"""
    assert _conn is not None, "数据库未初始化，请确保 lifespan 已启动"
    return _conn


async def init_db(db: aiosqlite.Connection) -> None:
    """创建表结构（幂等）。"""
    db.row_factory = _dict_factory  # type: ignore[assignment]
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS profile (
            id              INTEGER PRIMARY KEY CHECK (id = 1),
            name            TEXT NOT NULL,
            gender          TEXT NOT NULL,
            age             INTEGER NOT NULL,
            height_cm       REAL NOT NULL,
            weight_kg       REAL NOT NULL,
            body_fat_pct    REAL NOT NULL,
            target_weight_kg REAL NOT NULL,
            target_date     TEXT NOT NULL,
            activity_level  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS food (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            name                TEXT NOT NULL UNIQUE,
            calories_per_100g   REAL NOT NULL DEFAULT 0.0,
            protein_per_100g    REAL NOT NULL DEFAULT 0.0,
            carbs_per_100g      REAL NOT NULL DEFAULT 0.0,
            fat_per_100g        REAL NOT NULL DEFAULT 0.0,
            search_keywords     TEXT NOT NULL DEFAULT '[]',
            note                TEXT,
            created_at          TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS body_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date        TEXT NOT NULL UNIQUE,
            weight_kg       REAL NOT NULL,
            body_fat_pct    REAL NOT NULL,
            note            TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS circumference_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date        TEXT NOT NULL UNIQUE,
            waist_cm        REAL,
            arm_cm          REAL,
            thigh_cm        REAL,
            note            TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS diet_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            log_time      TEXT NOT NULL,
            food_name     TEXT NOT NULL,
            grams         REAL NOT NULL,
            note          TEXT,
            created_at    TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS exercise_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            log_time        TEXT NOT NULL,
            exercise_name   TEXT NOT NULL,
            duration_desc   TEXT NOT NULL,
            calories_kcal   REAL NOT NULL,
            note            TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)
    await db.commit()
