"""时区工具。

全程使用本地时区，序列化时携带时区偏移。
Windows 兼容：通过 UTC 偏移匹配 IANA 时区名。
"""

import zoneinfo
from datetime import datetime
from zoneinfo import ZoneInfo

_local_tz_cache: ZoneInfo | None = None


def local_tz() -> ZoneInfo:
    """获取系统本地时区。

    通过 UTC 偏移在可用时区列表中匹配，兼容 Windows 本地化名称。

    Returns:
        系统本地 ZoneInfo 对象。
    """
    global _local_tz_cache
    if _local_tz_cache is not None:
        return _local_tz_cache

    dt = datetime.now().astimezone()
    offset = dt.utcoffset()
    if offset is not None:
        naive = dt.replace(tzinfo=None)
        for name in zoneinfo.available_timezones():
            try:
                candidate = ZoneInfo(name)
                if candidate.utcoffset(naive) == offset:
                    _local_tz_cache = candidate
                    return candidate
            except Exception:
                continue

    _local_tz_cache = ZoneInfo("UTC")
    return _local_tz_cache


def now_local() -> datetime:
    """返回当前本地时间的 timezone-aware datetime。

    Returns:
        带时区信息的当前时间。
    """
    return datetime.now(local_tz())


def ensure_aware(dt: datetime) -> datetime:
    """确保 datetime 携带时区信息，缺失时补为本地时区。

    Args:
        dt: 可能无时区的 datetime。

    Returns:
        携带时区信息的 datetime。
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=local_tz())
    return dt


def format_local(dt: datetime) -> str:
    """格式化为 ISO 8601 字符串（含时区偏移）。

    Args:
        dt: 时区感知的 datetime。

    Returns:
        ISO 8601 格式字符串。
    """
    return ensure_aware(dt).isoformat()
