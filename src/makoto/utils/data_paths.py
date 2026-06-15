"""数据文件路径配置。

默认存储在项目运行目录下的 data/ 目录中。
可通过环境变量 MAKOTO_DATA_DIR 覆盖。
"""

from __future__ import annotations

import os
from pathlib import Path


def _data_dir() -> Path:
    """返回数据目录路径，可通过 MAKOTO_DATA_DIR 环境变量覆盖。"""
    env_val = os.environ.get("MAKOTO_DATA_DIR")
    if env_val:
        return Path(env_val)
    return Path("data")


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
