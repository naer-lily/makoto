"""终端输出配置。

统一管理 rich Console 实例，支持 --plain 纯文本模式。
当输出重定向（非 TTY）时自动降级为纯文本。
"""

from rich.console import Console

_plain: bool = False


def set_plain(plain: bool) -> None:
    """设置纯文本模式。

    Args:
        plain: True 时禁用所有样式。
    """
    global _plain
    _plain = plain


def get_console() -> Console:
    """获取共享 Console 实例。

    纯文本模式下 force_terminal=False，样式字符自动消失。

    Returns:
        rich Console 实例。
    """
    if _plain:
        return Console(force_terminal=False)
    return Console()
