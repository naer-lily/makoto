"""CLI 应用入口。"""

import typer

from makoto.commands.body import body_app
from makoto.commands.dashboard import dashboard_app
from makoto.commands.diet import diet_app
from makoto.commands.exercise import exercise_app
from makoto.commands.food import food_app
from makoto.commands.profile import profile_app
from makoto.utils import console as console_utils
from makoto.utils.profile_store import load as load_profile

app = typer.Typer(
    name="makoto",
    help="makoto — CLI 健身助手，记录身体数据、饮食与运动。",
    no_args_is_help=True,
)

_WHITELISTED = {"profile", "version"}
"""无需画像即可运行的命令。"""


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
    if sub is not None and sub not in _WHITELISTED and load_profile() is None:
        console = console_utils.get_console()
        console.print(
            "[red]尚未设置用户画像，请先执行 makoto profile set。[/red]"
        )
        raise typer.Exit(1)


app.add_typer(profile_app, name="profile", help="用户画像（设置/查看）")
app.add_typer(food_app, name="food", help="食物库管理（注册、搜索、查看）")
app.add_typer(body_app, name="body", help="身体测量记录")
app.add_typer(diet_app, name="diet", help="饮食记录")
app.add_typer(exercise_app, name="exercise", help="运动记录")
app.add_typer(dashboard_app, name="dashboard", help="数据总览（今日/历史）")


@app.command()
def version() -> None:
    """显示当前版本。"""
    from makoto import __version__

    typer.echo(f"makoto v{__version__}")
