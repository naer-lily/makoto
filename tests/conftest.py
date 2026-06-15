"""测试公共 fixtures。

提供内存 SQLite + TestClient + 鉴权绕过。
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import aiosqlite
import pytest
from fastapi.testclient import TestClient

from makoto.server.app import app
from makoto.server.auth import verify_token
from makoto.server.database import _dict_factory
from makoto.server.database import get_db
from makoto.server.database import init_db

TEST_TOKEN = "test-token-12345"


@pytest.fixture
async def test_db() -> AsyncGenerator[aiosqlite.Connection]:
    """创建内存数据库连接，建表后返回。每个测试函数独立连接。"""
    db = await aiosqlite.connect(":memory:")
    db.row_factory = _dict_factory  # type: ignore[assignment]
    await init_db(db)
    yield db
    await db.close()


@pytest.fixture
def client(test_db: aiosqlite.Connection) -> Any:
    """返回已 override get_db 和 verify_token 的 TestClient。"""

    async def _get_test_db() -> aiosqlite.Connection:
        return test_db

    def _bypass_auth() -> str:
        return TEST_TOKEN

    app.dependency_overrides[get_db] = _get_test_db
    app.dependency_overrides[verify_token] = _bypass_auth
    yield TestClient(app)
    app.dependency_overrides.clear()


def auth_headers() -> dict[str, str]:
    """Bearer token 请求头。"""
    return {"Authorization": f"Bearer {TEST_TOKEN}"}
