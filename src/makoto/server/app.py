"""FastAPI 应用入口。

makoto-server 启动 uvicorn，提供 REST API 服务。
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from makoto.server.auth import get_token
from makoto.server.database import connect
from makoto.server.database import disconnect
from makoto.server.database import init_db
from makoto.server.database import set_db_path
from makoto.server.routes import body
from makoto.server.routes import circumference
from makoto.server.routes import dashboard
from makoto.server.routes import diet
from makoto.server.routes import exercise
from makoto.server.routes import foods
from makoto.server.routes import profile


def _resolve_db_path() -> str:
    env = os.environ.get("MAKOTO_DATA_DIR")
    if env:
        return str(Path(env) / "makoto.db")
    root = Path(__file__).resolve().parent.parent.parent.parent
    return str(root / "data" / "makoto.db")


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    db_path = _resolve_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    set_db_path(db_path)
    db = await connect()
    await init_db(db)
    token = get_token()
    print(f"[makoto-server] 数据库: {db_path}")
    print(f"[makoto-server] Token: {token}")
    yield
    await disconnect()


app = FastAPI(
    title="makoto",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(profile.router)
app.include_router(foods.router)
app.include_router(body.router)
app.include_router(circumference.router)
app.include_router(diet.router)
app.include_router(exercise.router)
app.include_router(dashboard.router)

# 生产环境：挂载前端静态文件
_web_dir = Path(__file__).resolve().parent.parent.parent.parent / "web" / "dist"
if _web_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_web_dir), html=True), name="web")


def main() -> None:
    """makoto-server 入口。"""
    import uvicorn

    host = os.environ.get("MAKOTO_HOST", "0.0.0.0")
    port = int(os.environ.get("MAKOTO_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
