"""HTTP API 客户端封装。

对 makoto-server 的 REST API 做薄封装，供 CLI 命令调用。
"""

from __future__ import annotations

from typing import Any

import httpx

from makoto.client.config import ENDPOINT
from makoto.client.config import TOKEN
from makoto.client.config import ensure_token


class ClientError(Exception):
    """API 请求失败。"""

    def __init__(self, status: int, detail: str) -> None:
        self.status = status
        self.detail = detail
        super().__init__(f"{status}: {detail}")


class MakotoClient:
    """makoto-server HTTP 客户端。"""

    def __init__(self, endpoint: str = ENDPOINT, token: str = TOKEN) -> None:
        self._base = endpoint.rstrip("/")
        self._client = httpx.Client(
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )

    def _get(self, path: str, params: dict[str, str | int | None] | None = None) -> Any:
        if params:
            params = {k: v for k, v in params.items() if v is not None}
        resp = self._client.get(f"{self._base}{path}", params=params)
        return self._check(resp)

    def _post(self, path: str, data: dict[str, object]) -> Any:
        resp = self._client.post(f"{self._base}{path}", json=data)
        return self._check(resp)

    def _put(self, path: str, data: dict[str, object]) -> Any:
        resp = self._client.put(f"{self._base}{path}", json=data)
        return self._check(resp)

    def _delete(self, path: str) -> Any:
        resp = self._client.delete(f"{self._base}{path}")
        return self._check(resp)

    def _check(self, resp: httpx.Response) -> Any:
        if resp.is_success:
            return resp.json()
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise ClientError(resp.status_code, str(detail))

    # ── Profile ──

    def get_profile(self) -> dict[str, Any]:
        return self._get("/api/v1/profile")  # type: ignore[no-any-return]

    def set_profile(self, data: dict[str, object]) -> dict[str, Any]:
        return self._put("/api/v1/profile", data)  # type: ignore[no-any-return]

    # ── Foods ──

    def list_foods(self) -> list[dict[str, Any]]:
        return self._get("/api/v1/foods")  # type: ignore[no-any-return]

    def add_food(self, data: dict[str, object]) -> dict[str, Any]:
        return self._post("/api/v1/foods", data)  # type: ignore[no-any-return]

    def get_food(self, food_id: int) -> dict[str, Any]:
        return self._get(f"/api/v1/foods/{food_id}")  # type: ignore[no-any-return]

    def search_foods(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        return self._get(  # type: ignore[no-any-return]
            f"/api/v1/foods/search?q={query}&limit={limit}"
        )

    def delete_food(self, food_id: int) -> dict[str, Any]:
        return self._delete(f"/api/v1/foods/{food_id}")  # type: ignore[no-any-return]

    def update_food(self, food_id: int, data: dict[str, object]) -> dict[str, Any]:
        return self._put(f"/api/v1/foods/{food_id}", data)  # type: ignore[no-any-return]

    # ── Body Logs ──

    def list_body_logs(
        self, start: str | None = None, end: str | None = None
    ) -> list[dict[str, Any]]:
        return self._get(  # type: ignore[no-any-return]
            "/api/v1/body-logs", {"start": start, "end": end}
        )

    def create_body_log(self, data: dict[str, object]) -> dict[str, Any]:
        return self._post("/api/v1/body-logs", data)  # type: ignore[no-any-return]

    def delete_body_log(self, log_id: int) -> dict[str, Any]:
        return self._delete(f"/api/v1/body-logs/{log_id}")  # type: ignore[no-any-return]

    # ── Circumference Logs ──

    def list_circumference_logs(
        self, start: str | None = None, end: str | None = None
    ) -> list[dict[str, Any]]:
        return self._get(  # type: ignore[no-any-return]
            "/api/v1/circumference-logs", {"start": start, "end": end}
        )

    def create_circumference_log(self, data: dict[str, object]) -> dict[str, Any]:
        return self._post("/api/v1/circumference-logs", data)  # type: ignore[no-any-return]

    def delete_circumference_log(self, log_id: int) -> dict[str, Any]:
        return self._delete(  # type: ignore[no-any-return]
            f"/api/v1/circumference-logs/{log_id}"
        )

    # ── Diet Logs ──

    def list_diet_logs(
        self, limit: int = 50, start: str | None = None, end: str | None = None
    ) -> list[dict[str, Any]]:
        return self._get(  # type: ignore[no-any-return]
            "/api/v1/diet-logs", {"limit": limit, "start": start, "end": end}
        )

    def create_diet_log(self, data: dict[str, object]) -> dict[str, Any]:
        return self._post("/api/v1/diet-logs", data)  # type: ignore[no-any-return]

    def delete_diet_log(self, log_id: int) -> dict[str, Any]:
        return self._delete(f"/api/v1/diet-logs/{log_id}")  # type: ignore[no-any-return]

    def update_diet_log(self, log_id: int, data: dict[str, object]) -> dict[str, Any]:
        return self._put(f"/api/v1/diet-logs/{log_id}", data)  # type: ignore[no-any-return]

    # ── Exercise Logs ──

    def list_exercise_logs(
        self, limit: int = 50, start: str | None = None, end: str | None = None
    ) -> list[dict[str, Any]]:
        return self._get(  # type: ignore[no-any-return]
            "/api/v1/exercise-logs", {"limit": limit, "start": start, "end": end}
        )

    def create_exercise_log(self, data: dict[str, object]) -> dict[str, Any]:
        return self._post("/api/v1/exercise-logs", data)  # type: ignore[no-any-return]

    def delete_exercise_log(self, log_id: int) -> dict[str, Any]:
        return self._delete(f"/api/v1/exercise-logs/{log_id}")  # type: ignore[no-any-return]

    def update_exercise_log(self, log_id: int, data: dict[str, object]) -> dict[str, Any]:
        return self._put(f"/api/v1/exercise-logs/{log_id}", data)  # type: ignore[no-any-return]

    # ── Dashboard ──

    def dashboard_today(self) -> dict[str, Any]:
        return self._get("/api/v1/dashboard/today")  # type: ignore[no-any-return]

    def dashboard_report(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        params = []
        if start_date:
            params.append(f"start_date={start_date}")
        if end_date:
            params.append(f"end_date={end_date}")
        qs = "&" + "&".join(params) if params else ""
        return self._get(f"/api/v1/dashboard/report{qs}")  # type: ignore[no-any-return]


_client: MakotoClient | None = None


def get_client() -> MakotoClient:
    """获取共享 API 客户端单例。"""
    global _client
    if _client is None:
        ensure_token()
        _client = MakotoClient()
    return _client
