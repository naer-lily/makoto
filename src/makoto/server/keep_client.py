"""
Keep 运动数据客户端 — 通过逆向前端加密逻辑，从 Keep 后端直接拉取用户的图表数据。

背景:
  Keep 的运动档案页面 (https://show.gotokeep.com/sportpc-page/) 上的图表数据在传输
  过程中经过加密保护:
    - 前端先 GET  /common/uk              获取加密密钥 (明文)
    - 请求时 POST /query/submit           提交加密后的查询参数 (AES-128-CBC)
    - 异步轮询 GET  /query/queryResult    取回加密后的图表数据 (AES-128-CBC)

  加密方案为 AES-128-CBC, key=IV=UTF-8(userKey), PKCS7 填充, 密文以 Base64 传输。
  密钥由前端在页面初始化时从 /common/uk 获取，与 JWT 绑定。

  本脚本从 JS bundle (other.43a22.js) 逆向得到了前端的 encrypt() 和 decryptData()
  函数的完整逻辑，然后在 Python 中复现，从而可以绕过浏览器直接调用 API 获取数据。

  图表分为两类:
    - Dashboard 图表 (用户可配置): 通过 /dashboardChart/listByDashboardId 获取元信息
    - Home 页固定图表: 通过 frontKey 或 datasetId 直接查询，无需元信息

用法:
    python keep_client.py [dashboardId]

    JWT token 已内嵌为常量 (有效期 270 天, 至 2027-03-17)。

Public API:
    await Keep().get_readiness()       -- 运动准备程度 (home 页固定图表)
    await Keep().get_fitness(...)      -- 体能水平  ATL / CTL / TSB
    await Keep().get_weekly_load(...)  -- 周运动负荷 (近 N 周)
    await Keep().get_dashboard_data(did) -- 获取 dashboard 下所有图表的数据
    await Keep().parse_enif(enif_str)  -- 解密 submit 请求体中的 enif 字段
"""

# ruff: noqa: E501

from __future__ import annotations

import asyncio
import base64
import functools
import json
import time

import httpx
from Crypto.Cipher import AES
from pydantic import BaseModel
from pydantic import Field

TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJfaWQiOiI1ODlkY2E2ZTQ5MzMwMzc1NDUyYTY0MmMiLCJ1c2VybmFtZSI6IkFPWU1ZS04iLCJhdmF0YXIiOiJodHRwczovL3N0YXRpYzEua2VlcGNkbi5jb20vdXNlci1hdmF0YXIvMjAyNS8wNC8xOS8xMy81ODlkY2E2ZTQ5MzMwMzc1NDUyYTY0MmMvNTlmNjI1ODkyMTQxY2YzNDRiZjY5YjAyNWYzOWMzMThfMTAzOXgxMDM5LmpwZyIsIl92IjoiMSIsIl9lZCI6InlNRXFwb1M3NFh0NXpaU01JQ3NkTWc9PSIsImdlbmRlciI6Ik0iLCJkZXZpY2VJZCI6IiIsImlzcyI6Imh0dHBzOi8vd3d3LmdvdG9rZWVwLmNvbS8iLCJleHAiOjE4MDUyNzY3MjUsImlhdCI6MTc4MTk0ODcyNX0.wRvTSy35EhOfDWwCMn8XOfKi-xtphLZNO1M3eL67nV0"
_BASE = "https://api.gotokeep.com/sportpc-webapp"
_HEADERS: dict[str, str] = {
    "userRequestSource": "PC",
    "Origin": "https://show.gotokeep.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/140.0",
}


# ── Pydantic 实体 ────────────────────────────────────────


class ReadinessRecord(BaseModel):
    """运动准备程度 — 当前运动状态的综合评估"""

    recovery_hours: int = Field(alias="RECOVERY_TIME$recoverHours",
                                description="恢复时间 (小时)")
    readiness: int = Field(alias="SPORT_READINESS",
                           description="运动准备程度指数 (0–100)")
    level_name: str = Field(alias="levelDisplayName",
                            description="等级名称, e.g. 一般 / 良好 / 优秀")
    level_score: int = Field(alias="levelScore",
                             description="等级分数 (0–100)")


class FitnessRecord(BaseModel):
    """体能水平 — 单日的 ATL / CTL / TSB 值"""

    date: str = Field(description="日期, e.g. 2026.05.22")
    atl: int = Field(alias="SPORT_STATUS$ATL",
                     description="疲劳度 (Acute Training Load)")
    ctl: int = Field(alias="SPORT_STATUS$CTL",
                     description="体能水平 (Chronic Training Load)")
    tsb: int = Field(alias="SPORT_STATUS$TSB",
                     description="体能发展趋势 (Training Stress Balance)")


class WeeklyLoadRecord(BaseModel):
    """周运动负荷 — 单周的训练负荷与推荐负荷区间

    前端图表含两条信息:
      - 折线: 每周实际训练负荷 (training_load)
      - 阴影区间: 推荐负荷下界 → 上界 (load_lower → load_upper)
    """

    user_id: str = Field(alias="dim_1", description="用户 ID")
    week_start: str = Field(alias="dim_2", description="周起始日期")
    training_load: int | None = Field(default=None, alias="index_1",
                                         description="实际训练负荷 (部分周缺失)")
    load_lower: int = Field(alias="index_2",
                            description="推荐负荷下界")
    load_upper: int = Field(alias="index_3",
                            description="推荐负荷上界")


# ── 查询参数 ─────────────────────────────────────────────


class FitnessQuery(BaseModel):
    """体能水平 查询参数（仅可变部分）"""
    date_start: str = ""
    date_end: str = ""
    date_label: str = "近30天"


class WeeklyLoadQuery(BaseModel):
    """周运动负荷 查询参数（仅可变部分）"""
    week_count: int = 12
    date_label: str = "近12周"


# ── 异步缓存 ─────────────────────────────────────────────


def _async_ttl_cache(sec=300):
    """简易异步 TTL 缓存，只缓存最近一次结果。"""
    def deco(fn):
        @functools.wraps(fn)
        async def wrap(self):
            now = time.time()
            if not hasattr(wrap, "_v") or now - wrap._t > sec:
                wrap._v = await fn(self)
                wrap._t = now
            return wrap._v
        wrap._t = 0
        return wrap
    return deco


# ── Client ───────────────────────────────────────────────


class Keep:

    def __init__(self, token: str = TOKEN):
        self._token = token
        self._c = httpx.AsyncClient(
            base_url=_BASE,
            headers={**_HEADERS, "Authorization": f"Bearer {token}"},
            timeout=httpx.Timeout(30),
        )

    async def close(self):
        await self._c.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    # ── 网络 ──────────────────

    async def _get(self, path, **params):
        r = await self._c.get(path, params=params)
        r.raise_for_status()
        return r.json()

    async def _post(self, path, data=None):
        r = await self._c.post(path, json=data or {})
        r.raise_for_status()
        return r.json()

    # ── 密钥 ──────────────────

    @_async_ttl_cache(300)
    async def _uk(self):
        return (await self._get("/common/uk"))["data"]

    def _enc(self, uk: str | None, text):
        uk = (uk or "9a6e734a49d37625").encode()
        raw = text.encode()
        pad = 16 - len(raw) % 16
        raw += bytes([pad] * pad)
        return base64.b64encode(AES.new(uk, AES.MODE_CBC, iv=uk).encrypt(raw)).decode()

    @staticmethod
    def _dec(uk: str | None, b64):
        uk = (uk or "9a6e734a49d37625").encode()
        raw = AES.new(uk, AES.MODE_CBC, iv=uk).decrypt(base64.b64decode(b64))
        return json.loads(raw[:-raw[-1]].decode())

    # ── Dashboard 元数据 ──────

    async def _dashboards(self):
        return (await self._get("/dashboard/list"))["data"]

    async def _charts(self, did):
        return (await self._get("/dashboardChart/listByDashboardId", dashboardId=did))["data"]

    def _build_query(self, chart):
        q = {
            "frontKey": "", "datasetId": chart["datasetId"],
            "queryInfo": {"dimensions": chart["dimensions"], "indexs": chart["indexs"], "filters": []},
            "eventInfo": {"module": "统计分析", "subModule": chart["name"], "sportType": "", "tag1": "默认看板"},
        }
        for f in chart.get("filters", []):
            r = {"field": f["field"], "filterValue": f.get("value") or [],
                 "operatorType": "eq", "relation": "and",
                 "showName": f.get("showName"), "type": f["type"]}
            if f["field"] == "p_date":
                r["operatorType"] = "between"
                vc = f.get("valueCn") or []
                r["valueCn"] = vc[0] if vc else ""
            q["queryInfo"]["filters"].append(r)
        return q

    async def _submit(self, query):
        uk = await self._uk()
        payload = {"enif": self._enc(uk, json.dumps(query, ensure_ascii=False))}
        return (await self._post("/query/submit", payload))["data"]

    async def _poll(self, rid, timeout=120, interval=1):
        uk = await self._uk()
        deadline = time.time() + timeout
        while time.time() < deadline:
            d = (await self._get("/query/queryResult", queryRecordId=rid))["data"]
            if d["status"] == 2:
                return self._dec(uk, d["dataInfo"])
            if d["status"] in (0, 1) and d.get("recordId"):
                rid = d["recordId"]
            await asyncio.sleep(interval)
        raise TimeoutError("query timeout")

    async def _query_raw(self, query: dict) -> list | dict:
        """提交任意原始查询 dict，返回解密后未加工的 JSON"""
        rid = await self._submit(query)
        return await self._poll(rid)

    async def _query_chart(self, chart):
        rid = await self._submit(self._build_query(chart))
        return await self._poll(rid)

    # ── Public ──────────────────────────────────────

    async def parse_enif(self, enif_str: str) -> dict:
        """解密 submit 请求体中的 enif 字段为原始查询 dict"""
        uk = await self._uk()
        return self._dec(uk, enif_str)

    async def get_dashboard_data(self, did: int) -> dict:
        """获取 dashboard 下所有图表的数据

        Args:
            did: dashboard ID

        Returns:
            {"dashboardId": int, "charts": [{"name": str, "chartType": str,
             "datasetId": int, "data": list | dict}, ...]}
        """
        out = {"dashboardId": did, "charts": []}
        for c in await self._charts(did):
            try:
                data = await self._query_chart(c)
                out["charts"].append({
                    "name": c["name"], "chartType": c["chartType"],
                    "datasetId": c["datasetId"], "data": data,
                })
            except Exception as e:
                out["charts"].append({
                    "name": c["name"], "chartType": c["chartType"],
                    "datasetId": c["datasetId"], "error": str(e),
                })
        return out

    # ── 专用图表接口 ────────────────────────────────

    async def get_readiness(self) -> list[ReadinessRecord]:
        """获取运动准备程度 (Home 页固定图表)

        查询当前用户的运动准备程度、恢复时间、等级评估。

        Returns:
            List[ReadinessRecord] — 通常为单条记录
        """
        raw = await self._query_raw({"frontKey": "1_1_4"})
        return [ReadinessRecord.model_validate(r) for r in raw]

    async def get_fitness(self, q: FitnessQuery | None = None) -> list[FitnessRecord]:
        """获取体能水平 (ATL / CTL / TSB) 近 30 天数据

        前端对应图表: Home 页「体能水平」或 Dashboard「运动状态」

        Args:
            q: 可选查询参数, e.g. FitnessQuery(date_start="2026.05.20", date_end="2026.06.20")

        Returns:
            List[FitnessRecord]: 每日 ATL / CTL / TSB 数据
        """
        q = q or FitnessQuery()
        raw = await self._query_raw({
            "frontKey": "",
            "datasetId": 47,
            "queryInfo": {
                "dimensions": [
                    {"field": "date", "type": "date", "showName": "日期"},
                ],
                "indexs": [
                    {"field": "SPORT_STATUS$ATL", "showName": "疲劳度(ATL)", "value": "SPORT_STATUS$ATL",
                     "type": "number", "modelType": 1, "handler": '{"roundNumber":"0"}', "yAxisIndex": 1},
                    {"field": "SPORT_STATUS$CTL", "showName": "体能水平(CTL)", "value": "SPORT_STATUS$CTL",
                     "type": "number", "modelType": 1, "handler": '{"roundNumber":"0"}', "yAxisIndex": 1},
                    {"field": "SPORT_STATUS$TSB", "showName": "体能发展趋势(TSB)", "value": "SPORT_STATUS$TSB",
                     "type": "number", "modelType": 1, "handler": '{"roundNumber":"0"}', "yAxisIndex": 0},
                ],
                "filters": [
                    {"field": "rpc_index_list", "filterValue": [], "operatorType": "eq",
                     "relation": "and", "showName": "指标列表", "type": "string"},
                    {"field": "date_type", "filterValue": ["day"], "operatorType": "eq",
                     "relation": "and", "type": "string"},
                    {"field": "p_date", "filterValue": [
                        q.date_start, q.date_end,
                    ], "operatorType": "between", "relation": "and",
                     "showName": "", "type": "date",
                     "valueCn": q.date_label},
                ],
            },
        })
        return [FitnessRecord.model_validate(r) for r in raw]

    async def get_weekly_load(self, q: WeeklyLoadQuery | None = None) -> list[WeeklyLoadRecord]:
        """获取周运动负荷 (Home 页固定图表)

        前端图表含折线（实际负荷）+ 阴影区间（推荐负荷范围）。

        Args:
            q: WeeklyLoadQuery(week_count=12, date_label="近12周")

        Returns:
            List[WeeklyLoadRecord]:
                - user_id:      用户 ID
                - week_start:   周起始日期
                - training_load: 实际训练负荷 (部分周缺失)
                - load_lower:   推荐负荷下界
                - load_upper:   推荐负荷上界
        """
        q = q or WeeklyLoadQuery()
        raw = await self._query_raw({
            "frontKey": "",
            "datasetId": 65,
            "queryInfo": {
                "dimensions": [],
                "indexs": [],
                "filters": [
                    {"field": "p_date", "filterValue": [],
                     "valueCn": q.date_label},
                ],
            },
        })
        return [WeeklyLoadRecord.model_validate(r) for r in raw]


# ── CLI ──────────────────────────────────────────────────


async def _main():
    import sys
    k = Keep()

    if len(sys.argv) > 1 and sys.argv[1] in ("-r", "--readiness"):
        for r in await k.get_readiness():
            print(r.model_dump_json(indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] in ("-f", "--fitness"):
        for r in await k.get_fitness():
            print(r.model_dump_json(indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] in ("-w", "--weekly"):
        for r in await k.get_weekly_load():
            print(r.model_dump_json(indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] in ("-a", "--all"):
        for name, fn, limit in [
            ("readiness", k.get_readiness, 1),
            ("fitness", k.get_fitness, 3),
            ("weekly_load", k.get_weekly_load, 3),
        ]:
            try:
                rows = await fn()
                print(f"\n=== {name} ({len(rows)} records, showing {limit}) ===")
                for r in rows[:limit]:
                    print(r.model_dump_json(indent=2))
            except Exception as e:
                print(f"\n=== {name} ERROR: {e} ===")
    else:
        did = int(sys.argv[1]) if len(sys.argv) > 1 else 15246
        res = await k.get_dashboard_data(did)
        print(json.dumps(res, ensure_ascii=False, indent=2))

    await k.close()


if __name__ == "__main__":
    asyncio.run(_main())
