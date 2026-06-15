"""CLI 客户端配置。

从环境变量读取 API endpoint 和 token。
"""

from __future__ import annotations

import os

ENDPOINT = os.environ.get("MAKOTO_ENDPOINT", "http://127.0.0.1:8000")
TOKEN = os.environ.get("MAKOTO_TOKEN", "")

_warned = False


def ensure_token() -> None:
    """确保 TOKEN 已设置，未设置时输出一次警告。"""
    global _warned
    if not TOKEN and not _warned:
        _warned = True
        import sys

        print(
            "[makoto] 警告: MAKOTO_TOKEN 未设置，请设置环境变量后重试。",
            file=sys.stderr,
        )
