"""终端输出配置。

统一管理 rich Console 实例，支持自动/手动 Markdown 降级。
- 管道输出（非 TTY）自动降级为 Markdown，零样式字符
- --plain 强制 Markdown（覆盖终端模式）
"""

import sys

from rich.console import Console
from rich.table import Table

_plain: bool = False


def set_plain(plain: bool) -> None:
    """设置纯文本/Markdown 模式。

    Args:
        plain: True 时强制 Markdown 表格，无 ANSI 样式。
    """
    global _plain
    _plain = plain


def _should_use_plain() -> bool:
    """判断当前是否应输出纯文本。

    --plain 开启，或 stdout 不是 TTY（管道/重定向）时生效。
    """
    return _plain or not sys.stdout.isatty()


def is_plain() -> bool:
    """当前是否为纯文本模式（供外部查询）。"""
    return _should_use_plain()


def get_console() -> Console:
    """获取共享 Console 实例。

    纯文本/piped 模式下 force_terminal=False，ANSI 样式自动消失。

    Returns:
        rich Console 实例。
    """
    if _should_use_plain():
        return Console(force_terminal=False)
    return Console()


def _md_table(
    columns: list[str], rows: list[list[str]], align: list[str] | None = None
) -> str:
    """构建 Markdown 表格字符串。

    Args:
        columns: 列标题。
        rows: 数据行。
        align: 对齐方式列表 ("left" | "right")，默认全左。

    Returns:
        Markdown 表格文本。
    """
    if align is None:
        align = ["left"] * len(columns)

    seps: list[str] = []
    for a in align:
        if a == "right":
            seps.append("---:")
        else:
            seps.append("---")

    lines: list[str] = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(seps) + " |",
    ]
    for row in rows:
        padded = list(row)
        while len(padded) < len(columns):
            padded.append("")
        lines.append("| " + " | ".join(padded[: len(columns)]) + " |")

    return "\n".join(lines)


def render_table(
    columns: list[str],
    rows: list[list[str]],
    *,
    title: str = "",
    align: list[str] | None = None,
    col_styles: list[str] | None = None,
) -> None:
    """根据模式输出表格：piped/--plain → Markdown，终端 → rich Table。

    Args:
        columns: 列标题。
        rows: 数据行。
        title: 表格标题。
        align: 每列对齐方式 ("left" | "right")，默认全左。
        col_styles: rich 样式（仅在终端模式下生效）。
    """
    if _should_use_plain():
        if title:
            print(f"## {title}")
        print(_md_table(columns, rows, align))
    else:
        console = get_console()
        table = Table(title=title or None)
        for i, name in enumerate(columns):
            style = (
                (col_styles or [""] * len(columns))[i]
                if i < len(col_styles or [])
                else ""
            )
            just = (
                (align or ["left"] * len(columns))[i]
                if i < len(align or [])
                else "left"
            )
            table.add_column(name, style=style, justify=just)  # type: ignore[arg-type]
        for row in rows:
            table.add_row(*row)
        console.print(table)
