"""时区工具。

全项目统一的时区处理：

- server_tz()       — 服务时区（优先 MAKOTO_TZ 环境变量）
- today_local()      — 服务时区下的今天（date 对象）
- ensure_aware(dt)   — naive datetime 补上服务时区
- to_store_str(dt)   — 存储/传输格式：YYYY-MM-DDTHH:MM:SS（无偏移，SQLite date() 兼容）
- format_local(dt)   — 终端显示格式：YYYY-MM-DD HH:MM
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


def ensure_aware(dt: datetime) -> datetime:
    """确保 datetime 携带时区信息，naive 时补为服务端时区。

    Args:
        dt: 可能无时区的 datetime。

    Returns:
        携带时区信息的 datetime。
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=server_tz())
    return dt


def to_store_str(dt: datetime) -> str:
    """转换为存储/传输格式。

    使用本地时区，不含时区偏移后缀。
    SQLite 的 date() 函数对含偏移的字符串会做 UTC 换算，因此存储时统一去掉偏移。

    Args:
        dt: 任意 datetime（naive 或 aware）。

    Returns:
        "YYYY-MM-DDTHH:MM:SS" 格式字符串。
    """
    return ensure_aware(dt).strftime("%Y-%m-%dT%H:%M:%S")


def format_local(dt: datetime) -> str:
    """转换为终端显示格式。

    Args:
        dt: 任意 datetime（naive 或 aware）。

    Returns:
        "YYYY-MM-DD HH:MM" 格式字符串。
    """
    return ensure_aware(dt).strftime("%Y-%m-%d %H:%M")
