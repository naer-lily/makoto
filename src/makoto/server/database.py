"""SQLite 数据库连接管理（SQLModel + async SQLAlchemy）。

使用 ``sqlite+aiosqlite`` 异步驱动，通过 FastAPI lifespan 管理 engine 生命周期。
每个请求从 ``async_sessionmaker`` 取一个 ``AsyncSession``（``get_session`` 依赖）。

SQLite 默认关闭外键约束，连接时通过 ``PRAGMA foreign_keys=ON`` 显式启用。
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

import makoto.server.db_models  # noqa: F401  导入以注册全部表

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _enable_foreign_keys(engine: AsyncEngine) -> None:
    """为每个新连接启用 SQLite 外键约束。"""

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn: Any, _record: Any) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_engine(db_path: str) -> AsyncEngine:
    """创建并缓存 async engine + sessionmaker（应用启动时调用）。

    Args:
        db_path: SQLite 数据库文件路径。

    Returns:
        创建的 AsyncEngine。
    """
    global _engine, _sessionmaker
    url = f"sqlite+aiosqlite:///{Path(db_path).as_posix()}"
    _engine = create_async_engine(url, future=True)
    _enable_foreign_keys(_engine)
    _sessionmaker = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False
    )
    return _engine


async def create_db_and_tables(engine: AsyncEngine) -> None:
    """创建全部表（幂等，IF NOT EXISTS）。"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def dispose_engine() -> None:
    """释放 engine（应用关闭时调用）。"""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取请求级 AsyncSession（FastAPI 依赖注入用）。"""
    assert _sessionmaker is not None, "数据库未初始化，请确保 lifespan 已启动"
    async with _sessionmaker() as session:
        yield session
