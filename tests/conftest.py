"""测试公共 fixtures。

提供内存 SQLite（StaticPool 单连接复用）+ TestClient + 鉴权绕过。

async SQLite 内存库必须使用 StaticPool + 单连接，否则每次连接都是独立空库。
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

import makoto.server.db_models  # noqa: F401  注册全部表
from makoto.server.app import app
from makoto.server.auth import verify_token
from makoto.server.database import get_session

TEST_TOKEN = "test-token-12345"


@pytest.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """内存数据库 engine（StaticPool 单连接），建表后返回。每个测试独立。"""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn: Any, _record: Any) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def client(test_engine: AsyncEngine) -> Generator[TestClient, None, None]:
    """返回已 override get_session 和 verify_token 的 TestClient。"""
    sessionmaker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _get_test_session() -> AsyncGenerator[AsyncSession, None]:
        async with sessionmaker() as session:
            yield session

    def _bypass_auth() -> str:
        return TEST_TOKEN

    app.dependency_overrides[get_session] = _get_test_session
    app.dependency_overrides[verify_token] = _bypass_auth
    yield TestClient(app)
    app.dependency_overrides.clear()


def auth_headers() -> dict[str, str]:
    """Bearer token 请求头。"""
    return {"Authorization": f"Bearer {TEST_TOKEN}"}
