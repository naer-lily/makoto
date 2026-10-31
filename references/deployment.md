# makoto 部署与运维

> 工作目录：`/root/.hermes/skills/makoto`

## Docker 部署

```bash
cd /root/.hermes/skills/makoto
docker compose up -d    # 启动（端口 8788→8000）
docker compose down      # 停止
docker ps --filter "name=makoto"  # 检查状态
```

环境变量在 `.env` 中：
- `MAKOTO_ENDPOINT=http://10.19.76.1:8788`
- `MAKOTO_TOKEN=...`
- `MAKOTO_TZ=Asia/Shanghai`

## CLI 安装（Debian PEP 668）

```bash
pip3 install --break-system-packages --ignore-installed rich -e /root/.hermes/skills/makoto
```

## CLI 使用前

每次新终端会话必须：
```bash
export MAKOTO_ENDPOINT=http://10.19.76.1:8788
source /root/.hermes/skills/makoto/.env
```

## API 直调备选

当 CLI 未安装时可直接 curl：
```bash
source /root/.hermes/skills/makoto/.env
# 查食物
curl -s -H "Authorization: Bearer *** "$MAKOTO_ENDPOINT/api/v1/foods?limit=200"
# 今日总览
curl -s -H "Authorization: Bearer *** "$MAKOTO_ENDPOINT/api/v1/dashboard/today"
# 周/月报告
curl -s -H "Authorization: Bearer *** "$MAKOTO_ENDPOINT/api/v1/dashboard/report?range=week"
```

## Cron 时区注意

Hermes cron 使用**本地时区（北京时间 UTC+8）**，cron 表达式直接写北京时间，不需要 UTC 换算。之前错把北京时间转 UTC 导致凌晨触发。

## 迁移注意事项

迁移到新位置时，必须 `rsync` 整个项目目录（含 .git、data/、docker-compose.yml、Dockerfile、.env），不能只拷贝 SKILL.md + references/。迁移后 `docker compose down` 旧位置 → `docker compose up -d` 新位置。URL 和端口不变。下次 rsync 会走增量，只传差异文件。

## 内网 PWA 与公网入口（2026-10-28 起）

- 手机/内网入口：`https://10.19.76.1:8446/`；网关 `/opt/makoto-pwa`，systemd `makoto-pwa.service`，反向代理到 `http://127.0.0.1:8788`。
- API 只绑定 `127.0.0.1:8788`；CLI 的 `.env` 用 `MAKOTO_ENDPOINT=http://127.0.0.1:8788`。
- 前端构建和部署：`cd /root/.hermes/skills/makoto/web && npm run build`，然后 `/opt/makoto-pwa/deploy.sh`；脚本会同步 `web/dist` 到网关 public 并重启 `makoto-pwa`。
- `makoto.naer.ink` 的 cloudflared ingress 已移除，公网返回 404；不要为了内网访问重新加回。其它隧道站点（ghost/drop/staff）仍走 `/etc/cloudflared/config.yml`。
- 网关证书：`/opt/makoto-pwa/tls/makoto.crt`，由 `/opt/heaven-breaker-harness/secrets/tls/ca.crt` 签发，SAN 含 `10.19.76.1`、`127.0.0.1`、`localhost`。
- 排障顺序：`systemctl is-active makoto makoto-pwa` → `ss -ltnp | grep -E '8788|8446'` → `curl --cacert /opt/heaven-breaker-harness/secrets/tls/ca.crt https://10.19.76.1:8446/healthz` → 带 token 打 `/api/v1/dashboard/today`；公网 404 是预期。

## 服务不可达排障（10/11 建立）

主人报「makoto.naer.ink 打不开」时的检查链：

1. 从本机打域名取样本（5 发看稳定性/时延）：`for i in 1 2 3 4 5; do curl -o /dev/null -sS -w "%{http_code} %{time_total}s\n" --max-time 30 https://makoto.naer.ink/; sleep 1; done`
2. 容器：`docker ps`（makoto-makoto-server-1）＋ `docker logs --since 50m makoto-makoto-server-1 | grep -E 'HTTP/1.1" [45][0-9][0-9]'` 看错误码
3. 隧道：`systemctl status cloudflared`＋`journalctl -u cloudflared --since "40 min ago"`；路由在 `/etc/cloudflared/config.yml`（makoto.naer.ink → 127.0.0.1:8788）
4. 前端真渲染：browser_exec 开 https://makoto.naer.ink/ → 正常应停在「输入 Token 登录」
5. 以上全绿 ⇒ 问题在「他手机 → Cloudflare」段或设备本地：让他重试 / 切 Wi-Fi⇄流量 / 关代理；WG 在时旁路 `http://10.19.76.1:8788` 直连可绕开 CF 全段

协同技巧：他重试时看 `docker logs --since 2m` 有没有新 `GET /`——进来了=前端/缓存问题；没进来=网络段问题。首屏 JS 包约 1.1MB，国内走 CF 首开要几秒到十几秒，慢≠坏。
