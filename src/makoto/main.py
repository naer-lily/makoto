"""CLI 应用入口。"""

import typer

app = typer.Typer(
    name="makoto",
    help="makoto — CLI 健身助手，记录身体数据、饮食与运动。",
    no_args_is_help=True,
)


@app.callback()
def callback() -> None:
    """makoto 健身助手 CLI。"""


@app.command()
def version() -> None:
    """显示当前版本。"""
    from makoto import __version__

    typer.echo(f"makoto v{__version__}")
