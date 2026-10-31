# makoto Web PWA / 移动端适配说明

## PWA 外壳

- `public/manifest.webmanifest`
  - `name: makoto 健康数据`、`short_name: makoto`
  - `start_url: /`、`scope: /`、`display: standalone`
  - `background_color: #f5f7fa`、`theme_color: #409eff`
  - 192/512 普通图标 + 192/512 maskable 图标
- `public/icons/`
  - `icon-192.png`、`icon-512.png`：圆角普通图标
  - `maskable-192.png`、`maskable-512.png`：全出血、安全区内字标
  - `apple-touch-icon-180.png`：iOS 主屏图标
  - 图标为 makoto 字标 + 心电折线几何标记，不是页面截图。
- `index.html`
  - manifest、theme-color、favicon、apple touch icon
  - `apple-mobile-web-app-capable`、`apple-mobile-web-app-title`
- `src/main.ts`
  - 仅生产构建注册 `/sw.js`，`updateViaCache: 'none'`
  - 注册完成后立即调用 `registration.update()`
  - 监听 `visualViewport` 高度，写入 `--app-viewport-height`，供移动端 Dialog 收缩使用。

## Service Worker 缓存策略

文件：`public/sw.js`，`CACHE_VERSION = 'v1'`，缓存名前缀 `makoto-shell-`，当前缓存名 `makoto-shell-v1`。

| 请求类型 | 策略 |
| --- | --- |
| `/api/` 及子路径 | **network-only**；不读缓存、不写缓存，也不 `respondWith()` |
| 导航请求（`mode === 'navigate'`） | network-first；成功时更新缓存，失败回退缓存的 `index.html` / `/` |
| 构建后的 `/assets/*.js`、`/assets/*.css` | cache-first；首次未命中时联网并写入缓存 |
| manifest、`/icons/*` | 安装时预缓存，之后 cache-first |
| 其他同源 GET | 不拦截，保持浏览器默认行为 |

其他行为：

- `install`：预缓存 `/`、`/index.html`、manifest、全部图标，并读取构建产物 `/sw-assets.json` 预缓存所有路由 chunk 与 CSS；随后 `skipWaiting()`。
- `activate`：删除旧 `makoto-shell-*` 缓存，调用 `clients.claim()`。
- `sw-assets.json` 由 `vite.config.ts` 中的 `makoto-pwa-asset-manifest` 插件在构建时生成，覆盖懒加载路由 chunk，不依赖页面是否访问过。
- 缓存读取使用 `ignoreVary: true`。原因是 Vite preview/部分静态服务器会给资源返回 `Vary: Origin`，而带 `crossorigin` 的 module script 请求带 `Origin` 头；不忽略 Vary 会导致离线时缓存命中失败。
- 更新静态壳策略或行为时，递增 `CACHE_VERSION`；构建资源文件名本身带 hash。

## 移动端信息架构

断点：`< 768px`，共享 `src/composables/useMobile.ts`。

- 固定底部导航 5 格：
  - 总览 `/`
  - 饮食 `/diet`
  - 运动 `/exercise`
  - 身体 `/body`
  - 更多（打开现有抽屉）
- 底部导航最小触达高度 56px，含 `env(safe-area-inset-bottom)`；主内容底部预留
  `calc(72px + env(safe-area-inset-bottom))`。
- active 状态使用 Element Plus 主色变量，并对非四个主 tab 的页面高亮“更多”。
- “更多”抽屉保留全部入口：仪表盘、食物库、身体测量、饮食记录、运动记录、个人画像、围度记录、绘画记录、天气监视、退出登录。
- 桌面端保留左侧栏、折叠按钮和原有菜单结构；移动端顶部只保留菜单、makoto 字标和主题按钮，不显示桌面退出按钮。
- 抽屉/弹窗遮罩层 z-index 高于底部导航，避免导航浮在遮罩上方。

## 移动端内容适配

- 仪表盘统计卡：390px 下固定两列；5 张概览卡中的第 5 张跨两列，避免单张卡孤零零占一行；营养卡独占整行；图表统一单列。
- 日期范围：桌面保留原日期范围选择器（宽度约 350px）；移动端折叠为“日期范围”按钮，展开后显示日期选择器和重置。
- 以下表格在手机上切换为卡片列表，关键字段和编辑/删除按钮直接可点：
  - 食物库
  - 身体测量
  - 饮食记录
  - 运动记录
  - 围度记录
  - 绘画记录
  - 天气监视地点
- 仪表盘“今日饮食/今日运动/今日绘画”在手机上使用紧凑行卡片，避免表格横向滚动。
- 天气 7 天预报在手机上为两列卡片，24 小时预报保留横向滚动；页面本身无横向溢出。
- Dialog：
  - 宽度 `calc(100vw - 24px)`
  - 移动端表单标签置顶
  - footer 按钮等宽、至少 44px 高
  - 高度受 `--app-viewport-height` 限制，键盘弹出时 body 内部滚动，取消/保存在视口内
- 登录页卡片宽度 `min(400px, calc(100vw - 32px))`，主按钮全宽；矮视口顶部对齐。
- 个人画像：移动端标签置顶、计算结果单列、保存按钮全宽；Keep Token 改为密码输入框，默认不明文显示。
- 新颜色全部使用 Element Plus CSS 变量或现有主题变量；浅色/深色模式均验证。

## 内网部署

- 入口：`https://10.19.76.1:8446/`，复用 mist-breaker 内网 CA；手机需信任该根证书。
- `/opt/makoto-pwa/` 是网关，systemd `makoto-pwa.service` 以 `naer` 用户运行；只绑定 `10.19.76.1:8446`。
- 网关提供 PWA 静态壳和同源 `/api/` 反向代理，目标是 `127.0.0.1:8788` 的 makoto API；API 本身只绑定 `127.0.0.1:8788`，不再直接暴露到内网或公网。
- `/opt/makoto-pwa/deploy.sh` 会构建前端、同步 `web/dist` 到 `/opt/makoto-pwa/public` 并重启网关；静态文件改动不需要重启 API。
- 公网 `makoto.naer.ink` 的 Cloudflare Tunnel ingress 已移除，公网返回 404；其它隧道站点不受影响。
- PWA 安装需要 HTTPS；首次打开后由浏览器提示安装。Service Worker 只在生产构建注册。

## 已知边界

- PWA 安装需要 HTTPS（`localhost` 例外）；当前由 `/opt/makoto-pwa` 网关终止 TLS，systemd `makoto-pwa.service` 常驻。
- Service Worker 只在生产构建注册，开发模式交给 Vite HMR，避免开发缓存干扰。
- 离线时仅 app shell 可用；`/api/` 按需求 network-only，因此离线会显示网络错误、数据为空，不做离线数据写入或后台同步。
- 未实现 Push、Background Sync、Share Target、文件处理等额外 PWA 能力。
- 首次安装会预缓存所有路由 chunk（含 ECharts），首次安装流量较大；后续走缓存。
- 绘画热力图沿用原有 ECharts 日历实现，数据日期跨度较小时只展示该区间；390px 下容器不横向溢出。
- 现有鉴权仍是 localStorage token + Bearer 头，本次未改鉴权或后端接口。

## 自检记录

构建：

```bash
cd /root/.hermes/skills/makoto/web
npm run build
```

真实浏览器自检：

- 使用 `/opt/ui-venv/bin/python` + Playwright + `/usr/bin/chromium`
- 通过 `vite preview` 启动生产构建，`/api` 代理到内网服务
- token 从项目根 `.env` 读取，仅注入 localStorage；未打印、未写入源码/报告
- 视口：390×844、1440×1000
- 截图与 JSON 结果：`web/selfcheck/`
  - `results.json`：每页 overflow、底部导航遮挡、console error、导航与抽屉可达性
  - `extra-results.json`：Dialog 视口/键盘、天气预报、PWA 缓存与离线检查
  - `390x844-*-dark.png`：浅色/深色主题抽查截图
- 结果：所有页面 `scrollWidth <= innerWidth`；console error 0；底部导航未遮挡最后内容；四个主 tab 与“更多”抽屉全部可达；布局完整覆盖到视口底部。

注意：`web/selfcheck/` 为交付自检产物，不属于运行时资源；部署时不需要上传。
