"""天气监视 API 路由。

提供监视地点 CRUD + 天气预报缓存查询，通过 Open-Meteo 免费 API 获取数据。
每小时自动刷新，亦可手动触发。
"""

from __future__ import annotations

import json
from datetime import datetime

import httpx
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col
from sqlmodel import select

from makoto.server.auth import verify_token
from makoto.server.database import get_session
from makoto.server.db_models import WeatherCache
from makoto.server.db_models import WeatherWatch
from makoto.server.models import WeatherDay
from makoto.server.models import WeatherForecastResponse
from makoto.server.models import WeatherWatchCreate
from makoto.server.models import WeatherWatchResponse
from makoto.server.models import WeatherWatchUpdate
from makoto.utils.tz import server_tz
from makoto.utils.tz import to_store_str

router = APIRouter(prefix="/api/v1/weather", tags=["weather"])

# ── WMO 天气码 → 中文描述 ──

_WMO_DESC: dict[int, str] = {
    0: "晴天",
    1: "少云",
    2: "多云",
    3: "阴天",
    45: "有雾",
    48: "雾凇",
    51: "小毛毛雨",
    53: "中毛毛雨",
    55: "大毛毛雨",
    56: "冻毛毛雨",
    57: "冻毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "冻雨",
    67: "冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "阵雨",
    81: "中阵雨",
    82: "大阵雨",
    85: "小阵雪",
    86: "大阵雪",
    95: "雷阵雨",
    96: "雷阵雨+冰雹",
    99: "雷阵雨+冰雹",
}


def _wmo_desc(code: int) -> str:
    return _WMO_DESC.get(code, f"未知({code})")


# ── 响应转换 ──


def _watch_to_response(row: WeatherWatch) -> WeatherWatchResponse:
    assert row.id is not None
    return WeatherWatchResponse(
        id=row.id,
        label=row.label,
        latitude=row.latitude,
        longitude=row.longitude,
        created_at=row.created_at or "",
    )


def _build_forecast_response(
    watch: WeatherWatch, cache: WeatherCache | None
) -> WeatherForecastResponse:
    days: list[WeatherDay] = []
    fetched_at = ""
    if cache and cache.forecast_json:
        raw = json.loads(cache.forecast_json)
        daily = raw.get("daily", {})
        times = daily.get("time", [])
        tmax = daily.get("temperature_2m_max", [])
        tmin = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])
        precip_prob = daily.get("precipitation_probability_max", [])
        codes = daily.get("weathercode", [])
        for i in range(len(times)):
            days.append(
                WeatherDay(
                    date=str(times[i]),
                    temp_max=float(tmax[i]) if i < len(tmax) else 0.0,
                    temp_min=float(tmin[i]) if i < len(tmin) else 0.0,
                    precip_sum=float(precip[i]) if i < len(precip) else 0.0,
                    precip_probability=int(precip_prob[i]) if i < len(precip_prob) else 0,
                    weather_code=int(codes[i]) if i < len(codes) else 0,
                    weather_desc=_wmo_desc(int(codes[i])) if i < len(codes) else "",
                )
            )
        fetched_at = cache.fetched_at
    return WeatherForecastResponse(
        watch_id=watch.id,  # type: ignore[arg-type]
        label=watch.label,
        latitude=watch.latitude,
        longitude=watch.longitude,
        fetched_at=fetched_at,
        days=days,
    )


# ── Open-Meteo 拉取 ──


async def _fetch_from_open_meteo(lat: float, lon: float) -> str:
    """调用 Open-Meteo 获取 7 天预报，返回原始 JSON 字符串。"""
    url = "https://api.open-meteo.com/v1/forecast"
    params: dict[str, str | float | int] = {
        "latitude": lat,
        "longitude": lon,
        "daily": (
            "temperature_2m_max,temperature_2m_min,precipitation_sum,"
            "precipitation_probability_max,weathercode"
        ),
        "timezone": "Asia/Shanghai",
        "forecast_days": 7,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.text


async def _fetch_and_cache(
    watch_id: int, lat: float, lon: float, session: AsyncSession
) -> None:
    """拉取预报并写入缓存。"""
    forecast_json = await _fetch_from_open_meteo(lat, lon)
    now = to_store_str(datetime.now(server_tz()))

    existing = (
        await session.execute(
            select(WeatherCache).where(WeatherCache.watch_id == watch_id)
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing.forecast_json = forecast_json
        existing.fetched_at = now
    else:
        row = WeatherCache(watch_id=watch_id, forecast_json=forecast_json, fetched_at=now)
        session.add(row)


async def refresh_all_watches() -> None:
    """遍历所有监视地点，拉取并缓存天气预报（供定时任务和手动刷新调用）。"""
    from makoto.server.database import get_async_sessionmaker

    sm = get_async_sessionmaker()
    async with sm() as session:
        watches = (await session.execute(select(WeatherWatch))).scalars().all()
        if not watches:
            return
        for w in watches:
            assert w.id is not None
            try:
                await _fetch_and_cache(w.id, w.latitude, w.longitude, session)
            except Exception:
                logger.warning(f"刷新天气失败: watch_id={w.id} label={w.label}")
        await session.commit()


# ── 监视地点 CRUD ──


@router.get(
    "/watches",
    response_model=list[WeatherWatchResponse],
    summary="列出所有监视地点",
)
async def list_watches(
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> list[WeatherWatchResponse]:
    rows = (
        await session.execute(
            select(WeatherWatch).order_by(col(WeatherWatch.id))
        )
    ).scalars().all()
    return [_watch_to_response(r) for r in rows]


@router.post(
    "/watches",
    response_model=WeatherWatchResponse,
    status_code=201,
    summary="新增监视地点",
    description="添加一个天气监视地点，并立即拉取首次预报数据。",
)
async def create_watch(
    data: WeatherWatchCreate,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> WeatherWatchResponse:
    existing = (
        await session.execute(
            select(WeatherWatch).where(
                WeatherWatch.label == data.label
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"监视地点 '{data.label}' 已存在")

    row = WeatherWatch(label=data.label, latitude=data.latitude, longitude=data.longitude)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    assert row.id is not None

    try:
        await _fetch_and_cache(row.id, row.latitude, row.longitude, session)
        await session.commit()
    except Exception:
        logger.warning(f"首次拉取天气失败: watch_id={row.id} label={row.label}")

    return _watch_to_response(row)


@router.get(
    "/watches/{watch_id}",
    response_model=WeatherWatchResponse,
    summary="查看单个监视地点",
)
async def get_watch(
    watch_id: int,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> WeatherWatchResponse:
    row = (
        await session.execute(select(WeatherWatch).where(WeatherWatch.id == watch_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="监视地点不存在")
    return _watch_to_response(row)


@router.put(
    "/watches/{watch_id}",
    response_model=WeatherWatchResponse,
    summary="修改监视地点",
)
async def update_watch(
    watch_id: int,
    data: WeatherWatchUpdate,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> WeatherWatchResponse:
    row = (
        await session.execute(select(WeatherWatch).where(WeatherWatch.id == watch_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="监视地点不存在")

    if data.label is not None:
        dup = (
            await session.execute(
                select(WeatherWatch).where(
                    WeatherWatch.label == data.label,
                    WeatherWatch.id != watch_id,
                )
            )
        ).scalar_one_or_none()
        if dup is not None:
            raise HTTPException(status_code=409, detail=f"监视地点 '{data.label}' 已存在")
        row.label = data.label
    if data.latitude is not None:
        row.latitude = data.latitude
    if data.longitude is not None:
        row.longitude = data.longitude

    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _watch_to_response(row)


@router.delete(
    "/watches/{watch_id}",
    response_model=WeatherWatchResponse,
    summary="删除监视地点",
)
async def delete_watch(
    watch_id: int,
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> WeatherWatchResponse:
    row = (
        await session.execute(select(WeatherWatch).where(WeatherWatch.id == watch_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="监视地点不存在")

    result = _watch_to_response(row)
    cache = (
        await session.execute(
            select(WeatherCache).where(WeatherCache.watch_id == watch_id)
        )
    ).scalar_one_or_none()
    if cache is not None:
        await session.delete(cache)
    await session.delete(row)
    await session.commit()
    return result


# ── 天气预报查询 ──


@router.get(
    "/forecast",
    response_model=list[WeatherForecastResponse],
    summary="所有地点的缓存天气预报",
    description="返回所有监视地点的最新缓存预报。传 ?refresh=true 强制重新拉取。",
)
async def get_all_forecasts(
    refresh: bool = Query(False, description="是否强制刷新"),
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> list[WeatherForecastResponse]:
    if refresh:
        watches = (
            await session.execute(select(WeatherWatch))
        ).scalars().all()
        for w in watches:
            assert w.id is not None
            try:
                await _fetch_and_cache(w.id, w.latitude, w.longitude, session)
            except Exception:
                logger.warning(f"手动刷新失败: watch_id={w.id} label={w.label}")
        await session.commit()

    watches = (
        await session.execute(select(WeatherWatch).order_by(col(WeatherWatch.id)))
    ).scalars().all()
    results: list[WeatherForecastResponse] = []
    for w in watches:
        assert w.id is not None
        cache = (
            await session.execute(
                select(WeatherCache).where(WeatherCache.watch_id == w.id)
            )
        ).scalar_one_or_none()
        results.append(_build_forecast_response(w, cache))
    return results


@router.get(
    "/forecast/{watch_id}",
    response_model=WeatherForecastResponse,
    summary="单个地点的缓存天气预报",
    description="返回指定地点的最新缓存预报。传 ?refresh=true 强制重新拉取。",
)
async def get_forecast(
    watch_id: int,
    refresh: bool = Query(False, description="是否强制刷新"),
    _token: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> WeatherForecastResponse:
    watch = (
        await session.execute(select(WeatherWatch).where(WeatherWatch.id == watch_id))
    ).scalar_one_or_none()
    if watch is None:
        raise HTTPException(status_code=404, detail="监视地点不存在")
    assert watch.id is not None

    if refresh:
        try:
            await _fetch_and_cache(watch.id, watch.latitude, watch.longitude, session)
            await session.commit()
        except Exception:
            logger.warning(f"手动刷新失败: watch_id={watch.id}")

    cache = (
        await session.execute(
            select(WeatherCache).where(WeatherCache.watch_id == watch.id)
        )
    ).scalar_one_or_none()
    return _build_forecast_response(watch, cache)
