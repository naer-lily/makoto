"""数据文件路径配置。

未设 MAKOTO_DATA_DIR 时，默认使用项目根目录下的 data/ 目录。
"""

from __future__ import annotations

import os
from pathlib import Path

# 项目根目录 = 本文件往上 4 层 (utils → makoto → src → 项目根)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _data_dir() -> Path:
    """返回数据目录路径，可通过 MAKOTO_DATA_DIR 环境变量覆盖。"""
    env_val = os.environ.get("MAKOTO_DATA_DIR")
    if env_val:
        return Path(env_val)
    return _PROJECT_ROOT / "data"


def foods_path() -> Path:
    """返回食物库文件路径。"""
    return _data_dir() / "foods.jsonl"


def body_logs_path() -> Path:
    """返回身体测量记录文件路径。"""
    return _data_dir() / "body_logs.jsonl"


def diet_logs_path() -> Path:
    """返回饮食记录文件路径。"""
    return _data_dir() / "diet_logs.jsonl"


def exercise_logs_path() -> Path:
    """返回运动记录文件路径。"""
    return _data_dir() / "exercise_logs.jsonl"


def profile_path() -> Path:
    """返回用户画像文件路径。"""
    return _data_dir() / "profile.json"
