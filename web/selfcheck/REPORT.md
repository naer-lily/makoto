# makoto Web 自检报告

## 环境与命令

```bash
cd /root/.hermes/skills/makoto/web
npm run build
```

- 结果：成功（`vue-tsc -b && vite build`）。
- 自检：`/opt/ui-venv/bin/python` + Playwright + `/usr/bin/chromium`，`vite preview` 生产构建，`/api` 代理到内网服务。
- token：仅从项目根 `.env` 读取并注入 localStorage，未输出、未写入报告或源码。
- 截图目录：`web/selfcheck/`
- 机器结果：`web/selfcheck/results.json`、`web/selfcheck/extra-results.json`

## 页面 overflow 结果

所有页面 `document.documentElement.scrollWidth === window.innerWidth`、`document.body.scrollWidth === window.innerWidth`。

| 页面 | 390×844 | 1440×1000 |
| --- | --- | --- |
| 登录 | `390/390`，无溢出 | `1440/1440`，无溢出 |
| 仪表盘 | `390/390`，无溢出 | `1440/1440`，无溢出 |
| 食物库 | `390/390`，无溢出 | `1440/1440`，无溢出 |
| 身体测量 | `390/390`，无溢出 | `1440/1440`，无溢出 |
| 饮食记录 | `390/390`，无溢出 | `1440/1440`，无溢出 |
| 运动记录 | `390/390`，无溢出 | `1440/1440`，无溢出 |
| 个人画像 | `390/390`，无溢出 | `1440/1440`，无溢出 |
| 围度记录 | `390/390`，无溢出 | `1440/1440`，无溢出 |
| 绘画记录 | `390/390`，无溢出 | `1440/1440`，无溢出 |
| 天气监视 | `390/390`，无溢出 | `1440/1440`，无溢出 |

- console error：0。
- 390×844 底部导航：`navTop=787`，内容最大 `bottom=772`，9 个页面均未被遮挡。
- 四个主 tab：饮食 `/diet`、运动 `/exercise`、身体 `/body`、总览 `/` 全部点击跳转通过。
- “更多”抽屉：可见，包含 9 个菜单项 + 退出登录。
- Dialog：6 个新增/编辑弹窗在 390 宽下均为 `366px`（左右各 12px），
  footer 可见；390×500（模拟键盘）下再次测得 footer 仍可见，内容区内部滚动。
- 天气预报页：390 下无页面横向溢出；7 天卡片 2 列，24 小时条仅在卡片内部横向滚动。
- PWA：`makoto-shell-v1` 缓存 38 个 shell 资源，`sw-assets.json` 中资源全部命中，
  `/api/` 缓存条目为 0；离线导航 `/foods` 可加载 shell 与底部导航。
- 深色主题抽查（`390x844-dashboard-dark.png`、`390x844-foods-dark.png`）：变量颜色正常，无不可读文本。

## 截图路径

移动端 `390×844`：

- `web/selfcheck/390x844-login.png`
- `web/selfcheck/390x844-dashboard.png`
- `web/selfcheck/390x844-foods.png`
- `web/selfcheck/390x844-body.png`
- `web/selfcheck/390x844-diet.png`
- `web/selfcheck/390x844-exercise.png`
- `web/selfcheck/390x844-profile.png`
- `web/selfcheck/390x844-circumference.png`
- `web/selfcheck/390x844-painting.png`
- `web/selfcheck/390x844-weather.png`

桌面端 `1440×1000`：同名文件前缀为 `1440x1000-`。

补充：

- `390x844-more-drawer.png`
- `390x844-weather-forecast.png`
- `390x844-dialog-*.png`（6 个新增/编辑弹窗）
- `390x500-keyboard-*.png`（模拟键盘高度）
- `390x844-*-dark.png`（深色主题）
- `390x844-offline-foods.png`（离线 shell）

## read_image 实际观察

- 登录页 390：卡片居中、宽度未超出视口，输入框和登录按钮完整显示。
- 仪表盘 390：统计卡为稳定两列；第五张“净热量”跨整行，不存在单卡独占一行；
  四个 tab 完整、无左右箭头；日期范围折叠为按钮；底部导航未盖住卡片。
- 食物库 390：表格已变为卡片；每张卡片可看到营养字段与编辑/删除按钮，
  无需横向拖动；搜索框与添加按钮同一行且未溢出。
- 身体测量 390：卡片显示日期、体重、体脂率、备注和删除按钮；触达面积充足。
- 饮食/运动 390：时间、名称、克数/时长、热量与宏量营养均在卡片内；
  编辑/删除按钮完整可见。
- 个人画像 390：标签在输入框上方，输入控件占满行宽；Keep Token 为密码框，
  截图中无明文 token；主按钮便于触达。
- 围度记录 390：四项围度以 2×2 字段展示，备注和删除按钮可见。
- 绘画记录 390：热力图在卡片宽度内，无横向溢出；记录卡片显示时长和备注；
  源数据中空的 `file_id` 显示为“未记录”，不出现空白字段。
- 天气监视 390：地点表单、地点卡片完整；预报为两列日卡，小时预报内部横滑；
  页面无横向溢出。最后一张日卡可能单独占一行，这是列表数量导致，不属于统计卡布局问题。
- 桌面端：左侧栏、折叠按钮、表格列和日期范围选择器均保留；日期选择器恢复紧凑宽度。
- 弹窗：390 宽下宽度 366px，左右留 12px；键盘高度 500px 时保存/取消仍可见，
  弹窗 body 滚动而不是把按钮顶出屏幕。
- 离线 `/foods`：shell 与底部导航正常出现；因 `/api/` 强制 network-only，
  页面显示 Network Error 和空数据，符合预期。
