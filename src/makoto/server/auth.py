"""Bearer Token 鉴权。

服务端从 MAKOTO_TOKEN 环境变量读取 token，客户端请求须携带
Authorization: Bearer <token> 头。
"""

from __future__ import annotations

import os

from fastapi import HTTPException
from fastapi import Security
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

security = HTTPBearer()


def get_token() -> str:
    """读取服务端 token，未设置时生成随机 token 并打印。"""
    token = os.environ.get("MAKOTO_TOKEN")
    if not token:
        import secrets

        token = secrets.token_urlsafe(32)
        print(f"[makoto-server] MAKOTO_TOKEN 未设置，已生成随机 token: {token}")
        os.environ["MAKOTO_TOKEN"] = token
    return token


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """FastAPI 依赖：验证 Bearer token 是否与服务端一致。"""
    if credentials.credentials != get_token():
        raise HTTPException(status_code=403, detail="无效的 token")
    return credentials.credentials
