"""CLI 应用入口。

命令模块延迟加载，避免 pydantic-core 编译阻塞启动。
"""

from __future__ import annotations

import importlib
from typing import Any

import typer

from makoto.utils import console as console_utils

app = typer.Typer(
    name="makoto",
    help="makoto — CLI 健身助手，记录身体数据、饮食与运动。",
    no_args_is_help=True,
)

_WHITELISTED = {"profile", "version"}
"""无需画像即可运行的命令。"""


class _LazyApp:
    """typer.Typer 懒加载代理。

    仅在 subcommand 实际被调用时才 import 对应模块，
    避免启动时加载所有命令引发的 pydantic-core 编译开销。
    """

    def __init__(self, module_path: str, attr: str) -> None:
        self._module_path = module_path
        self._attr = attr
        self._app: Any = None

    def _load(self) -> typer.Typer:
        if self._app is None:
            mod = importlib.import_module(self._module_path)
            self._app = getattr(mod, self._attr)
        return self._app  # type: ignore[no-any-return]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._load(), name)


@app.callback()
def callback(
    ctx: typer.Context,
    plain: bool = typer.Option(
        False, "--plain", help="纯文本输出，禁用颜色与样式（输出给 AI 时使用）"
    ),
) -> None:
    """makoto 健身助手 CLI。"""
    console_utils.set_plain(plain)

    sub = ctx.invoked_subcommand
    if sub is not None and sub not in _WHITELISTED:
        # 延迟导入 profile_store（依赖 pydantic）
        from makoto.utils.profile_store import load as load_profile

        if load_profile() is None:
            console = console_utils.get_console()
            console.print(
                "[red]尚未设置用户画像，请先执行 makoto profile set。[/red]"
            )
            raise typer.Exit(1)


app.add_typer(
    _LazyApp("makoto.commands.food", "food_app"),  # type: ignore[arg-type]
    name="food",
    help="食物库管理（注册、搜索、查看）",
)
app.add_typer(
    _LazyApp("makoto.commands.body", "body_app"),  # type: ignore[arg-type]
    name="body",
    help="身体测量记录",
)
app.add_typer(
    _LazyApp("makoto.commands.diet", "diet_app"),  # type: ignore[arg-type]
    name="diet",
    help="饮食记录",
)
app.add_typer(
    _LazyApp("makoto.commands.exercise", "exercise_app"),  # type: ignore[arg-type]
    name="exercise",
    help="运动记录",
)
app.add_typer(
    _LazyApp("makoto.commands.profile", "profile_app"),  # type: ignore[arg-type]
    name="profile",
    help="用户画像（设置/查看）",
)
app.add_typer(
    _LazyApp("makoto.commands.dashboard", "dashboard_app"),  # type: ignore[arg-type]
    name="dashboard",
    help="数据总览（今日/历史）",
)


@app.command()
def version() -> None:
    """显示当前版本。"""
    from makoto import __version__

    typer.echo(f"makoto v{__version__}")
