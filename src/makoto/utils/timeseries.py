"""时序数据处理工具。

提供纯函数式的时间序列填充、插值与滑动窗口计算。
"""

from datetime import date
from datetime import timedelta
from typing import TypeVar

T = TypeVar("T")
"""值类型变量。"""


def date_series(start: date, end: date) -> list[date]:
    """生成连续日期序列（含起止）。

    Args:
        start: 起始日期。
        end: 结束日期。

    Returns:
        按升序排列的连续日期列表。
    """
    n = (end - start).days
    return [start + timedelta(days=i) for i in range(n + 1)]


def forward_fill(
    series: dict[date, T],
    dates: list[date],
) -> dict[date, tuple[T, bool]]:
    """前值填充：缺失日期沿用最近一条已知值。

    日期必须升序，第一个已知值之前的日期不会被填充。

    Args:
        series: 稀疏的 {日期: 值} 映射。
        dates: 待填充的完整日期序列（升序）。

    Returns:
        {日期: (值, 是否原始)} 映射。is_original=False 表示值来自前值继承。
    """
    result: dict[date, tuple[T, bool]] = {}
    last_val: T | None = None

    for d in sorted(dates):
        if d in series:
            last_val = series[d]
            result[d] = (last_val, True)
        elif last_val is not None:
            result[d] = (last_val, False)

    return result


def linear_interpolate(
    series: dict[date, float],
    dates: list[date],
) -> dict[date, tuple[float, bool]]:
    """线性插值：在已知数据点之间做平滑过渡。

    已知点之间的 gap 按天数线性等分；超出已知范围的日期
    取最近端点的值（等价于前/后值填充）。

    Args:
        series: 稀疏的 {日期: 浮点值} 映射。
        dates: 待填充的完整日期序列（升序）。

    Returns:
        {日期: (值, 是否原始)} 映射。is_original=False 表示值为插值或端点填充。
    """
    sorted_dates = sorted(dates)
    known = [(d, series[d]) for d in sorted_dates if d in series]

    if not known:
        return {}

    result: dict[date, tuple[float, bool]] = {}

    # 首段：第一个已知值之前的所有日期填该值
    first_d, first_v = known[0]
    for d in sorted_dates:
        if d < first_d:
            result[d] = (first_v, False)

    # 中间段落：逐段线性插值
    for i in range(len(known) - 1):
        d1, v1 = known[i]
        d2, v2 = known[i + 1]
        gap_days = (d2 - d1).days

        for j in range(gap_days + 1):
            d = d1 + timedelta(days=j)
            if d not in result:  # 避免重复写入（上一段的末尾 == 下一段的起点）
                if j == 0 or j == gap_days:
                    result[d] = (v1 if j == 0 else v2, True)
                else:
                    interp = v1 + (v2 - v1) * (j / gap_days)
                    result[d] = (round(interp, 1), False)

    # 尾段：最后一个已知值之后的所有日期填该值
    last_d, last_v = known[-1]
    for d in sorted_dates:
        if d > last_d:
            result[d] = (last_v, False)

    return result


def rolling_mean(
    series: dict[date, float],
    window: int,
) -> dict[date, float]:
    """滑动窗口均值。

    每个日期的均值 = 含自身往前 window 天内的所有有效值的平均。
    窗口起始处不足 window 天则用实际天数。

    Args:
        series: {日期: 值} 映射（需已填充完整）。
        window: 窗口大小（天）。

    Returns:
        {日期: 滑动均值} 映射。
    """
    sorted_dates = sorted(series.keys())
    result: dict[date, float] = {}

    for i, d in enumerate(sorted_dates):
        start_idx = max(0, i - window + 1)
        window_vals = [series[sorted_dates[j]] for j in range(start_idx, i + 1)]
        result[d] = round(sum(window_vals) / len(window_vals), 1)

    return result
