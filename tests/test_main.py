"""测试 CLI 入口。"""

from typer.testing import CliRunner

from makoto.main import app

runner = CliRunner()


def test_version() -> None:
    """验证 `makoto version` 输出正确版本号。"""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "makoto v0.1.0" in result.stdout
