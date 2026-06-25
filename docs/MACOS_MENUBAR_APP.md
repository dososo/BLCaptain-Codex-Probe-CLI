# macOS 状态栏 App

BLCaptain Codex Probe Bar 是 BLCaptain Codex Probe CLI 的原生 macOS 状态栏入口。它不是新的账本引擎，而是把现有 CLI 的本地会话账本、预算预警、数据源可信度和 Dashboard 入口放进系统菜单栏。

## 适合解决的问题

- 不想每次记 `codex-probe sessions`、`alerts`、`dashboard` 命令。
- 想随时看当前 Codex 会话是否已经高风险。
- 想一键生成/打开本地 Dashboard 和报告目录。
- 想保留 CLI 的 local-first 隐私边界，但降低普通用户使用门槛。

## 构建

先确保当前仓库已经安装 CLI：

```bash
scripts/setup-local.sh
```

构建 `.app`：

```bash
scripts/macos/build-codex-probe-bar.sh
```

生成位置：

```text
build/CodexProbeBar.app
```

可以直接双击，或运行：

```bash
open build/CodexProbeBar.app
```

注意：这个入口是本地构建体验版。它适合开发者、本地验证和公开 beta；如果要给普通用户发 release 包，必须走 Developer ID 签名、notarization 公证和 Gatekeeper 验证。完整流程见 [macOS 正式分发、签名与公证](MACOS_RELEASE_DISTRIBUTION.md)。

## 面板能力

状态栏点击后会显示：

- token delta 总量。
- 会话数。
- 本地预算预警数。
- 最高消耗会话和建议动作。
- 预算预警摘要。
- 数据源可信度摘要。
- 本地隐私边界。

可执行动作：

- 刷新：重新读取本地账本 JSON 输出。
- 采集一次：调用 `codex-probe watch once`。
- 打开 Dashboard：生成并打开本地 HTML Dashboard。
- 报告目录：打开本地报告目录。
- 隐私报告：生成并打开本地隐私报告。
- 退出：关闭状态栏 App。

## 配置

App 会优先读取环境变量，其次读取 app bundle 内的 `Resources/defaults.json`，最后使用用户目录默认值。

| 配置 | 环境变量 | 默认 |
|---|---|---|
| CLI 路径 | `CODEX_PROBE_CLI` | 自动寻找 `codex-probe` |
| DB 路径 | `CODEX_PROBE_DB` | `~/.codex-probe/probe.db` |
| 报告目录 | `CODEX_PROBE_REPORTS_DIR` | `~/CodexProbeReports/ledger` |
| 时间范围 | `CODEX_PROBE_RANGE` | `7d` |
| 工作目录 | `CODEX_PROBE_PROJECT_DIR` | 用户主目录或构建脚本写入的仓库路径 |

构建脚本会写入默认配置：

- CLI：优先使用当前仓库 `.venv/bin/codex-probe`。
- DB：`~/.codex-probe/probe.db`。
- 报告：`~/CodexProbeReports/ledger`。
- 工作目录：当前仓库根目录。

## 隐私边界

状态栏 App 只调用本地 `codex-probe --json` 命令。

它不会：

- 登录 OpenAI、ChatGPT 或 Codex。
- 读取浏览器 cookie。
- 读取 OpenAI token。
- 读取钥匙串或系统凭据。
- 抓包、代理或拦截请求。
- 读取聊天正文、prompt、assistant 输出或工具参数。
- 上传报告、数据库或统计数据。

如果 CLI 没有可用数据源，App 会显示空状态或错误提示，不会伪造用量。

## 当前发布边界

第一版状态栏 App 是公开 beta 级桌面入口。本地构建出来的 `.app` 默认未签名、未公证，不能承诺普通用户下载后完全没有 Gatekeeper 提示。

当前本地体验版不包含：

- Apple Developer ID 签名。
- notarization 公证。
- 自动登录项。
- 菜单栏偏好设置窗口。
- 官方账单读取。
- 多工具账本。

本仓库已提供签名、公证、打包和 preflight 脚本，但真正签名/公证需要维护者自己的 Apple Developer 账号与证书。完整分发不应以读取登录态或浏览器数据为代价。
