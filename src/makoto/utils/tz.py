"""时区工具。

服务端通过 MAKOTO_TZ 环境变量配置时区（默认自动检测系统时区）。
CLI 侧通过 ensure_aware 确保 datetime 携带时区信息。
"""

from __future__ import annotations

import os
import zoneinfo
from datetime import date
from datetime import datetime
from zoneinfo import ZoneInfo

_local_tz_cache: ZoneInfo | None = None
_server_tz_cache: ZoneInfo | None = None


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


def server_tz() -> ZoneInfo:
    """获取服务端时区。

    优先读取 MAKOTO_TZ 环境变量，未设置则回退到系统本地时区。

    Returns:
        服务端 ZoneInfo 对象。
    """
    global _server_tz_cache
    if _server_tz_cache is not None:
        return _server_tz_cache

    env_tz = os.environ.get("MAKOTO_TZ", "").strip()
    if env_tz:
        try:
            _server_tz_cache = ZoneInfo(env_tz)
            return _server_tz_cache
        except Exception:
            pass

    _server_tz_cache = local_tz()
    return _server_tz_cache


def today_local() -> date:
    """返回服务端时区的今日日期。

    Returns:
        服务端时区下的今天。
    """
    return datetime.now(server_tz()).date()


def now_local() -> datetime:
    """返回当前本地时间的 timezone-aware datetime。

    Returns:
        带时区信息的当前时间。
    """
    return datetime.now(local_tz())


def ensure_aware(dt: datetime) -> datetime:
    """确保 datetime 携带时区信息，缺失时补为服务端时区。

    Args:
        dt: 可能无时区的 datetime。

    Returns:
        携带时区信息的 datetime。
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=server_tz())
    return dt


def format_local(dt: datetime) -> str:
    """格式化为 ISO 8601 字符串（含时区偏移）。

    Args:
        dt: 时区感知的 datetime。

    Returns:
        ISO 8601 格式字符串。
    """
    return ensure_aware(dt).isoformat()
