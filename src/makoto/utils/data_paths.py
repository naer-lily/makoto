"""数据文件路径配置。

默认存储在项目运行目录下的 data/ 目录中。
可通过环境变量 MAKOTO_DATA_DIR 覆盖。
"""

from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class DataConfig(BaseSettings):
    """数据目录配置。

    Attributes:
        data_dir: 数据文件存放目录。
    """

    model_config = SettingsConfigDict(
        env_prefix="MAKOTO_",
        frozen=True,
    )

    data_dir: Path = Path("data")


_data_config = DataConfig()
"""全局数据配置单例。"""


def foods_path() -> Path:
    """返回食物库文件路径。"""
    return _data_config.data_dir / "foods.jsonl"


def body_logs_path() -> Path:
    """返回身体测量记录文件路径。"""
    return _data_config.data_dir / "body_logs.jsonl"


def diet_logs_path() -> Path:
    """返回饮食记录文件路径。"""
    return _data_config.data_dir / "diet_logs.jsonl"


def exercise_logs_path() -> Path:
    """返回运动记录文件路径。"""
    return _data_config.data_dir / "exercise_logs.jsonl"
