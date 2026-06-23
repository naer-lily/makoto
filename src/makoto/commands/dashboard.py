"""数据总览命令（CLI 客户端）。"""

from __future__ import annotations

import json

import typer

from makoto.client.api import ClientError
from makoto.client.api import get_client
from makoto.utils.console import get_console
from makoto.utils.console import render_table

dashboard_app = typer.Typer(no_args_is_help=True)


@dashboard_app.command()
def today() -> None:
    """查看今日数据总览。"""
    console = get_console()
    cli = get_client()
    try:
        data = cli.dashboard_today()
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    console.print(f"\n[bold underline]{data['date']} 数据总览[/bold underline]\n")

    # 身体
    console.print("[bold]身体[/bold]")
    body = data.get("body")
    if body is None:
        console.print("  [dim]本日未录入[/dim]")
    else:
        console.print(f"  体重: {body['weight_kg']} kg    体脂率: {body['body_fat_pct']}%")
        if body.get("note"):
            console.print(f"  [dim]备注: {body['note']}[/dim]")

    # 围度
    circ = data.get("circumference")
    if circ is not None:
        parts: list[str] = []
        if circ.get("waist_cm"):
            parts.append(f"腰围: {circ['waist_cm']} cm")
        if circ.get("arm_cm"):
            parts.append(f"臂围: {circ['arm_cm']} cm")
        if circ.get("thigh_cm"):
            parts.append(f"大腿围: {circ['thigh_cm']} cm")
        if parts:
            console.print(f"  [bold]围度[/bold]  {'  '.join(parts)}")

    # 饮食
    diets = data.get("diets", [])
    console.print(f"\n[bold]饮食[/bold] ({len(diets)} 条)")
    console.print(f"  NETEE 非运动总消耗:  {data['netee_kcal']:.0f} kcal/天")
    console.print("          (BMR × 活动系数 = 不含刻意运动的一日基线)")

    if diets:
        diet_rows: list[list[str]] = []
        for d in diets:
            diet_rows.append([
                str(d.get("food_name", "")),
                f"{d.get('grams', 0):.0f}g",
                f"{d.get('calories_kcal', 0):.0f} kcal",
                f"{d.get('protein_g', 0):.1f}g",
                f"{d.get('carbs_g', 0):.1f}g",
                f"{d.get('fat_g', 0):.1f}g",
            ])
        render_table(
            columns=["食物", "克数", "热量", "蛋白质", "碳水", "脂肪"],
            rows=diet_rows,
            align=["left", "right", "right", "right", "right", "right"],
            col_styles=["green", "", "yellow", "", "", ""],
        )
        total_intake = data.get("total_intake_kcal", 0)
        total_protein = data.get("total_protein_g", 0)
        total_carbs = data.get("total_carbs_g", 0)
        total_fat = data.get("total_fat_g", 0)
        console.print(
            f"  [bold]合计: {total_intake:.0f} kcal"
            f"  P:{total_protein:.1f}g  C:{total_carbs:.1f}g  F:{total_fat:.1f}g[/bold]"
        )
    else:
        console.print("  [dim]本日未录入[/dim]")

    # 运动
    exercises = data.get("exercises", [])
    total_burned = data.get("total_burned_kcal", 0)
    console.print(f"\n[bold]运动[/bold] ({len(exercises)} 条)")
    if exercises:
        ex_rows: list[list[str]] = [
            [r["exercise_name"], r["duration_desc"], f"{r['calories_kcal']:.0f} kcal"]
            for r in exercises
        ]
        render_table(
            columns=["运动", "时长/数量", "消耗"],
            rows=ex_rows,
            align=["left", "left", "right"],
            col_styles=["green", "", "yellow"],
        )
        console.print(f"  运动消耗:      {total_burned:.0f} kcal")
    else:
        console.print("  [dim]本日未录入[/dim]")

    # 净热量
    netee = data.get("netee_kcal", 0)
    net = data.get("net_kcal", 0)
    total_intake = data.get("total_intake_kcal", 0)

    console.print("\n[bold underline]净热量[/bold underline]")
    console.print(f"  NETEE  {netee:>8.0f} kcal")
    console.print(f"  运动   +{total_burned:>6.0f} kcal")
    console.print(f"  摄入   -{total_intake:>6.0f} kcal")
    console.print(f"  {'─' * 22}")
    if net > 0:
        label = "[green]缺口[/green]"
    elif net < 0:
        label = "[yellow]盈余[/yellow]"
    else:
        label = "平衡"
    console.print(f"  {label}  {abs(net):>8.0f} kcal")


@dashboard_app.command()
def report(
    start_date: str | None = typer.Option(
        None, "--start-date", "-s", help="起始日期 (YYYY-MM-DD)，默认从首条记录开始"
    ),
    end_date: str | None = typer.Option(
        None, "--end-date", "-e", help="结束日期 (YYYY-MM-DD)，默认到目标日期"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="以 JSON 格式输出原始数据"
    ),
) -> None:
    """多日趋势报告：体重/体脂率/FFM/七日均线 + 每日热量缺口。"""
    console = get_console()
    cli = get_client()
    try:
        data = cli.dashboard_report(start_date, end_date)
    except ClientError as e:
        console.print(f"[red]请求失败: {e.detail}[/red]")
        raise typer.Exit(1) from e

    if json_output:
        console.print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    rows_data = data.get("rows", [])
    summary = data.get("summary", {})

    table_rows: list[list[str]] = []
    first_w = 0.0
    last_w = 0.0
    first_bf = 0.0
    last_bf = 0.0
    first_ffm = 0.0
    last_ffm = 0.0
    first_mw = 0.0
    last_mw = 0.0
    first_mb = 0.0
    last_mb = 0.0
    first_mf = 0.0
    last_mf = 0.0

    for i, rd in enumerate(rows_data):
        w_val = float(rd.get("weight_kg", 0))
        bf_val = float(rd.get("body_fat_pct", 0))
        ffm_val = float(rd.get("ffm_kg", 0))
        mw_val = float(rd.get("ma_weight_kg", 0))
        mb_val = float(rd.get("ma_body_fat_pct", 0))
        mf_val = float(rd.get("ma_ffm_kg", 0))
        bal_val = float(rd.get("deficit_kcal", 0))
        exp_val = rd.get("expected_deficit_kcal")
        interp = bool(rd.get("is_interpolated", False))

        sign = "+" if bal_val > 0 else ""
        bal_str = f"{sign}{bal_val:.0f} kcal"
        exp_str = f"{exp_val:.0f} kcal" if exp_val is not None else "-"

        w_str = f"{w_val:.1f} kg{'*' if interp else ''}"
        bf_str = f"{bf_val:.1f}%{'*' if interp else ''}"
        ffm_str = f"{ffm_val:.1f} kg{'*' if interp else ''}"
        mw_str = f"{mw_val:.1f} kg"
        mb_str = f"{mb_val:.1f}%"
        mf_str = f"{mf_val:.1f} kg"

        if i == 0:
            first_w, first_bf, first_ffm = w_val, bf_val, ffm_val
            first_mw, first_mb, first_mf = mw_val, mb_val, mf_val
        last_w, last_bf, last_ffm = w_val, bf_val, ffm_val
        last_mw, last_mb, last_mf = mw_val, mb_val, mf_val

        table_rows.append([
            str(rd.get("date", "")), w_str, bf_str, ffm_str,
            mw_str, mb_str, mf_str, bal_str, exp_str,
        ])

    w_delta = last_w - first_w
    bf_delta = last_bf - first_bf
    ffm_delta = last_ffm - first_ffm
    mw_delta = last_mw - first_mw
    mb_delta = last_mb - first_mb
    mf_delta = last_mf - first_mf
    total_balance = float(summary.get("total_deficit_kcal", 0))
    total_expected = summary.get("total_expected_kcal")
    exp_total_str = f"{total_expected:.0f} kcal" if total_expected is not None else "-"

    table_rows.append([
        f"[bold]总计 ({data.get('days', 0)}天)[/bold]",
        f"[bold]{w_delta:+.1f} kg[/bold]",
        f"[bold]{bf_delta:+.1f}%[/bold]",
        f"[bold]{ffm_delta:+.1f} kg[/bold]",
        f"[bold]{mw_delta:+.1f} kg[/bold]",
        f"[bold]{mb_delta:+.1f}%[/bold]",
        f"[bold]{mf_delta:+.1f} kg[/bold]",
        f"[bold]{total_balance:+.0f} kcal[/bold]",
        f"[bold]{exp_total_str}[/bold]",
    ])

    title_text = f"{data['start_date']} ~ {data['end_date']} ({data['days']} 天)"
    render_table(
        columns=[
            "日期", "体重", "体脂率", "FFM",
            "7日均重", "7日均脂", "7均FFM", "热量缺口", "日期望",
        ],
        rows=table_rows,
        title=title_text,
        align=["left"] + ["right"] * 8,
        col_styles=["cyan", "", "", "", "", "", "", "yellow", "dim"],
    )

    has_interp = any(bool(r.get("is_interpolated")) for r in rows_data)
    if has_interp:
        console.print("[dim]* 标记表示该值来自插值或前值继承[/dim]")

    met = summary.get("met_target")
    if met is False and total_expected is not None:
        console.print(
            f"[red]实际缺口 {total_balance:.0f} < 期望 {total_expected:.0f} kcal，未达标[/red]"
        )
    elif met is True:
        console.print(
            f"[green]实际缺口 {total_balance:.0f} >= 期望 {total_expected:.0f} kcal，达标[/green]"
        )
