# 菜单栏 App / 桌面组件评估

目标：给 BLCaptain Codex Probe CLI 提供更友好的桌面入口，但不以读取 OpenAI 登录态、浏览器 cookie、token、钥匙串或系统凭据为代价。

## 结论

当前优先推荐：

1. **原生 macOS 状态栏 App：BLCaptain Codex Probe Bar**
2. **本地 HTML Dashboard + Watcher 状态页**
3. **macOS LaunchAgent 显式启动 watcher**
4. **Raycast / Alfred / Shell 快捷入口**

v0.9.0 已实现极薄原生状态栏 App。它只调用本地 `codex-probe --json`，不读取登录态、cookie、token 或钥匙串。完整签名、公证、自动更新和登录项仍作为后续独立发布工程处理。

## 候选方案

| 方案 | 用户价值 | 实现成本 | 隐私风险 | 推荐度 |
|---|---|---:|---:|---|
| 本地 HTML Dashboard | 低门槛查看会话排行、项目汇总、周报和隐私说明 | 低 | 低 | 高 |
| Watcher 状态页 | 看后台采集是否运行、最近日志和最近高消耗会话 | 低 | 低 | 高 |
| Raycast / Alfred 快捷入口 | 一键打开 Dashboard 或运行 `codex-probe setup` | 低 | 低 | 中高 |
| macOS 菜单栏 App | 更像产品，适合长期驻留提醒 | 中 | 低 | 高 |
| Electron/Tauri 桌面 App | 跨平台视觉更完整 | 高 | 中 | 暂不推荐 |
| 浏览器扩展 | 可贴近官方页面 | 高 | 高 | 不推荐 |

## 推荐路径

### 第一阶段：轻入口

- 保留 `codex-probe setup --demo`。
- 保留 `codex-probe dashboard --open`。
- 保留 `codex-probe watch status-page --open`。
- README 提供 Codex 桌面版一句话安装和打开 Dashboard 的提示词。

验收标准：

- 用户不懂 Python，也能让 Codex 桌面版安装并打开本地 Dashboard。
- 不读取浏览器 cookie、token、钥匙串或系统凭据。
- 不上传任何数据。

### 第二阶段：快捷启动器

提供 Raycast / Alfred 示例命令：

```bash
cd /path/to/BLCaptain-Codex-Probe-CLI
.venv/bin/codex-probe --db .probe/probe.db dashboard --range 7d --open
```

或：

```bash
cd /path/to/BLCaptain-Codex-Probe-CLI
.venv/bin/codex-probe --db .probe/probe.db watch status-page --open
```

验收标准：

- 快捷入口只调用本地 CLI。
- 不新增后台权限。
- 不读取登录态。

### 第三阶段：菜单栏 App 原型（v0.9.0 已实现）

已经提供一个极薄 Swift/AppKit wrapper：

- 面板项：查看 token 摘要、最高消耗会话、预算预警、数据源可信度和隐私边界。
- 操作项：刷新、采集一次、生成/打开 Dashboard、打开报告目录、打开隐私报告、退出。
- 只调用本地 `codex-probe` 命令。
- 不嵌入浏览器自动化。
- 不读取 cookie、token、钥匙串或 OpenAI 登录态。
- 不做网络上传。

验收标准：

- 用户能看懂每个菜单项会执行什么本地命令。
- 首次运行前明确显示隐私边界。
- 所有业务数据仍存在用户本地 `.probe/` 或用户指定 DB。

## 明确不做

- 不读取 OpenAI / Codex 登录态。
- 不读取浏览器 cookie。
- 不读取钥匙串或系统凭据。
- 不抓包、不代理、不拦截 Codex 请求。
- 不把报告上传到云端。
- 不伪造官方账单或 token 数字。

## 当前版本建议

当前版本应把「状态栏 App + Dashboard + Watcher 状态页 + Codex 桌面版提示词」作为对外发布入口。签名、公证、自动更新和自动登录项可以作为后续独立里程碑，而不是 v0.9.0 的阻塞项。
