"""用户画像持久化。

以单文件 JSON 存储于 data/profile.json。
"""

from __future__ import annotations

from makoto.models.profile import UserProfile
from makoto.utils.data_paths import profile_path


def load() -> UserProfile | None:
    """从文件加载用户画像。

    Returns:
        用户画像实例，不存在时返回 None。
    """
    filepath = profile_path()
    if not filepath.exists():
        return None
    return UserProfile.model_validate_json(filepath.read_text(encoding="utf-8"))


def save(profile: UserProfile) -> None:
    """保存用户画像到文件。

    Args:
        profile: 用户画像实例。
    """
    filepath = profile_path()
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(profile.model_dump_json(indent=2), encoding="utf-8")
