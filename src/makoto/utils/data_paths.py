"""数据文件路径配置。

未设 MAKOTO_DATA_DIR 时，默认使用项目根目录下的 data/ 目录。
"""

from __future__ import annotations

import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _data_dir() -> Path:
    env_val = os.environ.get("MAKOTO_DATA_DIR")
    if env_val:
        return Path(env_val)
    return _PROJECT_ROOT / "data"


def db_path() -> Path:
    """返回 SQLite 数据库路径。"""
    return _data_dir() / "makoto.db"
