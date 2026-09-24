"""CLI 客户端 dashboard report 的 URL 构建回归测试。

2026-09-24：修复 `dashboard_report` 查询串前缀错误（`&` → `?`），
此前带 -s/-e 参数的调用会 404（查询串被并进路径）。
"""

import httpx

from makoto.client.api import MakotoClient


def _make_client(seen: dict[str, str]) -> MakotoClient:
    """构造一个用 MockTransport 捕获请求 URL 的客户端。"""

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"rows": [], "summary": {}})

    client = MakotoClient(endpoint="http://test", token="t")
    client._client = httpx.Client(
        transport=httpx.MockTransport(handler),
        headers={"Authorization": "Bearer t"},
    )
    return client


def test_dashboard_report_query_string_uses_question_mark() -> None:
    seen: dict[str, str] = {}
    client = _make_client(seen)
    client.dashboard_report("2026-06-01", "2026-06-08")
    assert seen["url"] == (
        "http://test/api/v1/dashboard/report?start_date=2026-06-01&end_date=2026-06-08"
    )


def test_dashboard_report_without_params_has_no_query() -> None:
    seen: dict[str, str] = {}
    client = _make_client(seen)
    client.dashboard_report()
    assert seen["url"] == "http://test/api/v1/dashboard/report"


def test_dashboard_report_partial_params() -> None:
    seen: dict[str, str] = {}
    client = _make_client(seen)
    client.dashboard_report(start_date="2026-06-01")
    assert seen["url"] == "http://test/api/v1/dashboard/report?start_date=2026-06-01"
