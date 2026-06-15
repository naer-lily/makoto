"""CLI 应用入口。"""

import typer

from makoto.commands.body import body_app
from makoto.commands.diet import diet_app
from makoto.commands.exercise import exercise_app
from makoto.commands.food import food_app
from makoto.utils import console as console_utils

app = typer.Typer(
    name="makoto",
    help="makoto — CLI 健身助手，记录身体数据、饮食与运动。",
    no_args_is_help=True,
)


@app.callback()
def callback(
    plain: bool = typer.Option(
        False, "--plain", help="纯文本输出，禁用颜色与样式（输出给 AI 时使用）"
    ),
) -> None:
    """makoto 健身助手 CLI。"""
    console_utils.set_plain(plain)


app.add_typer(food_app, name="food", help="食物库管理（注册、搜索、查看）")
app.add_typer(body_app, name="body", help="身体测量记录")
app.add_typer(diet_app, name="diet", help="饮食记录")
app.add_typer(exercise_app, name="exercise", help="运动记录")


@app.command()
def version() -> None:
    """显示当前版本。"""
    from makoto import __version__

    typer.echo(f"makoto v{__version__}")
