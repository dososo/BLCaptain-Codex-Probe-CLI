# BLCaptain Codex Probe CLI

> 本地优先的 Codex 会话级 Token 账本、用量治理与 Skill / 输出质量体检 CLI。它帮你定位 token/credits 消耗在哪个会话、哪个项目、哪个时间段，并解释为什么贵、怎么降配、什么时候该停。

[English README](README.en.md)

![Python](https://img.shields.io/badge/Python-%3E%3D3.10-2b2622.svg)
![CLI](https://img.shields.io/badge/Type-CLI-d98e3a.svg)
![Local First](https://img.shields.io/badge/Data-Local--First-2f5ea7.svg)
![Release](https://img.shields.io/badge/Release-v0.9.0-4b5563.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

> **Codex 桌面版最快入口**
>
> 打开这个仓库目录，把下面任意一段发给 Codex。
>
> 安全体验 demo，不读取你的真实历史：
>
> ```text
> 请运行 scripts/setup-local.sh，只使用仓库 demo 样本生成 Codex 用量 Dashboard，不读取我的真实 Codex 历史、浏览器 cookie、token、钥匙串或系统凭据，不上传任何数据。最后告诉我 Dashboard 和报告路径。
> ```
>
> 分析自己的本地 Codex 会话：
>
> ```text
> 请用 BLCaptain Codex Probe CLI 分析我本地 Codex 最近 7 天的会话 token 用量。先 dry-run 检查可用数据源，再只读取 token 用量白名单字段，生成 reports/ledger/dashboard.html、sessions.md、ledger-report.md、project-summary.md、weekly-report.md、timeline.md、alerts.md、source-confidence.md、task-report.md 和 privacy-report.md。最后用普通话告诉我：哪个会话最贵、哪个项目最贵、哪段时间增长最快、主要消耗在哪类任务、为什么贵、怎么降配、什么时候该停。不要读取聊天正文、浏览器 cookie、token、钥匙串或系统凭据，不要上传任何数据。
> ```
>
> 只分析一次 `/status`：
>
> ```text
> 我会粘贴 Codex /status，请先脱敏明显的 key、cookie、token、邮箱和手机号，保存到 .probe/my-status.txt，再用 BLCaptain Codex Probe CLI 生成 reports/my-usage-report.md，并解释为什么贵、怎么降配、什么时候该停。不要读取浏览器 cookie、token、钥匙串或系统凭据，不要上传任何数据。
> ```

> **安装与体验**
>
> 在 Codex 桌面版里也可以直接说：
>
> ```text
> 帮我安装这个仓库 https://github.com/dososo/BLCaptain-Codex-Probe-CLI。安装完成后先运行安全 demo，只使用仓库示例数据生成 Codex 用量 Dashboard，不读取我的真实 Codex 历史、浏览器 cookie、token、钥匙串或系统凭据，不上传任何数据。
> ```
>
> 也可以手动运行：
>
> ```bash
> git clone https://github.com/dososo/BLCaptain-Codex-Probe-CLI.git
> cd BLCaptain-Codex-Probe-CLI
> scripts/setup-local.sh
> ```
>
> 无参数时会跑安全 demo：创建 `.venv`、安装 CLI、初始化账本、dry-run、导入仓库 synthetic 样本、生成并打开 Dashboard。
>
> 如果想体验 macOS 状态栏入口：
>
> ```bash
> scripts/macos/build-codex-probe-bar.sh
> open build/CodexProbeBar.app
> ```
>
> 这是本地体验版。GitHub 开源、CLI 安装和用户本地构建不需要 Apple Developer ID；只有维护者发布给普通用户双击安装的 `.app` / `.dmg` 时，才需要考虑签名、公证和 Gatekeeper 验证。见 [macOS 正式分发、签名与公证](docs/MACOS_RELEASE_DISTRIBUTION.md)。
>
> 轻量安装方式见 [安装方式](docs/INSTALL.md)，包括 uvx、pipx 和 Homebrew Formula 草案。

---

## 它是什么

BLCaptain Codex Probe CLI 是一个本地命令行工具，不是 Codex Skill，也不是 OpenAI 官方 dashboard。

当前推荐发布定位：**CLI 是正式开源主入口，macOS 状态栏 App 是可选本地构建体验版**。因此 GitHub 开源发布不需要 Apple Developer Program；签名、公证只适用于维护者未来分发可双击安装的 Mac App。

v0.9.0 在真实数据源接入、稳定 watcher、项目聚合、周报和阶段级治理之上，新增 **原生 macOS 状态栏 App**。它把 CLI 的会话账本、预算预警、数据源可信度和 Dashboard 入口放进系统菜单栏，优先回答这件事：

> 到底是哪条 Codex 会话、哪个项目、哪个阶段、哪类任务烧掉了 token/credits？现在该继续、降配，还是先停？

它同时保留两个旧能力：

1. **任务级 `/status` 用量报告**：解释一次任务为什么贵、怎么降配、什么时候该停。
2. **Skill / 输出质量体检**：检查 AI 味、插件风险、敏感信息和隐私边界缺口。

如果本机 Codex 结构化 rollout 日志里存在 token 用量字段，它可以在本地自动导入历史会话用量；如果数据源没有 token 字段，它只会导入元信息或明确说明无法精确归因，不会伪造数字。

它不会承诺省钱，不会绕过额度，不会读取登录态，也不会替代官方账单。它更像一个本地账本和刹车片：让你少在长会话里无意识烧上下文。

## 工作效果

### macOS 状态栏 App

v0.9.0 新增 BLCaptain Codex Probe Bar：一个原生 macOS 菜单栏入口。它不重复实现账本逻辑，而是调用本地 `codex-probe --json`，展示最高消耗会话、token 总量、预算预警、数据源可信度和常用动作。

```bash
scripts/macos/build-codex-probe-bar.sh
open build/CodexProbeBar.app
```

详见 [macOS 状态栏 App](docs/MACOS_MENUBAR_APP.md)。

发布边界必须讲清楚：仓库本地构建的 `.app` 默认未签名、未公证，只能作为本地体验或 beta 验证；这不影响 CLI 作为 GitHub 开源项目发布。未来如果维护者要提供普通用户双击安装的 `.app` / `.dmg`，再使用 [macOS 正式分发、签名与公证](docs/MACOS_RELEASE_DISTRIBUTION.md) 中的签名、公证、stapling、Gatekeeper preflight 和打包流程。

### 会话级 Token 账本

本地账本会按时间范围输出会话排行，每条会话都带上 token delta、credits delta、项目、数据源、置信度和建议动作。

示例报告：

- [会话排行报告](examples/reports/ledger/sessions.md)
- [单会话详情报告](examples/reports/ledger/session-readme-release.md)
- [总账报告](examples/reports/ledger/ledger-report.md)
- [项目级汇总报告](examples/reports/ledger/project-summary.md)
- [Codex 周报](examples/reports/ledger/weekly-report.md)
- [阶段级时间线报告](examples/reports/ledger/timeline.md)
- [本地预算预警报告](examples/reports/ledger/alerts.md)
- [数据源可信度报告](examples/reports/ledger/source-confidence.md)
- [任务类型归因报告](examples/reports/ledger/task-report.md)
- [隐私审计报告](examples/reports/ledger/privacy-report.md)
- [本地 HTML Dashboard](examples/reports/ledger/dashboard.html)

<p>
  <img src="assets/screenshots/ledger-dashboard.png" alt="本地 Codex 会话级 Token 账本 Dashboard" width="100%">
</p>

模型列来自导入数据源中的 `model` 字段。CLI 会原样展示官方导出、快照或本地 rollout 提供的模型名；如果数据源没有模型字段，会显示为空或未知，不会猜测或强行改写。

### 保留能力：任务级报告与 Skill 体检

| 任务级用量报告 | Skill / 输出质量体检 |
|---|---|
| <img src="assets/screenshots/usage-report-preview.svg" alt="任务级用量报告效果" width="100%"> | <img src="assets/screenshots/skill-lint-preview.svg" alt="Skill / 输出质量体检效果" width="100%"> |
| 把 `total_tokens`、上下文余量、5 小时/7 天额度和「继续、降配、停止」决策放在同一视图。 | 标出 AI 味、插件风险、敏感信息和隐私边界缺口，并展示脱敏后的证据片段。 |

## 命名约定

| 用途 | 名称 |
|---|---|
| 产品名 | BLCaptain Codex Probe CLI |
| GitHub 仓库名 | `BLCaptain-Codex-Probe-CLI` |
| Python 包名 | `blcaptain-codex-probe` |
| 公开命令 | `codex-probe` |
| 短别名 | `probe` |
| 兼容命令 | `blcaptain-codex-probe`、`codex-usage-skill-probe` |
| macOS 状态栏 App | BLCaptain Codex Probe Bar |

为什么不叫 Skill：它不是给 Agent 读取的 Skill 指令包，而是用户和 Agent 都可以调用的本地 CLI。它可以检查 Skill，但它本身不是 Skill。

## 核心能力

| 能力 | 命令 | 结果 |
|---|---|---|
| 一键本地 setup | `scripts/setup-local.sh` 或 `codex-probe setup --demo` | 安装/初始化、dry-run、报告、Dashboard 一次完成 |
| macOS 状态栏 App | `scripts/macos/build-codex-probe-bar.sh` | 原生菜单栏入口，展示风险摘要并打开 Dashboard / 报告 |
| macOS 发布检查 | `scripts/macos/preflight-codex-probe-bar.sh` | 检查状态栏 App bundle、签名、公证、Gatekeeper 和禁用隐私越界能力 |
| 数据源安全检查 | `codex-probe sources doctor` | 显示可用数据源、最高置信度和隐私边界 |
| 深度数据源检查 | `codex-probe sources doctor --deep` | 安全检查本机 Codex rollout 字段覆盖率，只输出哈希和计数 |
| 初始化本地账本 | `codex-probe ledger init` | 创建 SQLite schema 和隐私审计记录 |
| 检查官方导出 | `codex-probe ledger inspect-export <file>` | 识别 CSV / JSON / JSONL 字段和推荐映射 |
| 生成字段映射 | `codex-probe ledger map-export <file> --out mapping.json` | 生成可编辑 mapping JSON |
| 导入官方导出 | `codex-probe ledger import --official-export <file>` | 支持 CSV / JSON / JSONL，exact 置信度会话归因 |
| 导入本地历史 | `codex-probe ledger import-history --source local-codex` | 从本机 Codex rollout 白名单字段导入历史 token 快照 |
| 导入本地快照 | `codex-probe ledger import --snapshot <file>` | high / medium / low 置信度 delta 归因 |
| 单次采集 | `codex-probe watch once` | 执行一次安全 local history 采集 |
| 后台采集 | `codex-probe watch start/status/logs/stop` | PID、状态、日志、最近采集时间、错误和采集次数 |
| 会话排行 | `codex-probe sessions --range 7d` | 找到最耗 token 的会话 |
| 项目汇总 | `codex-probe projects --range 30d` | 找到最耗 token 的项目、最高消耗会话和置信度分布 |
| Codex 周报 | `codex-probe weekly-report --range 30d` | 按本地时区 ISO 周复盘会话、项目和高消耗周 |
| 阶段级时间线 | `codex-probe timeline --range 30d` | 找到会话内 token delta 增长最快的时间区间、阶段标签和建议动作 |
| 本地预算预警 | `codex-probe alerts --range 30d` | 基于本地阈值输出单会话、项目、总账和上下文停止线 |
| 任务类型归因 | `codex-probe task-report --range 30d` | 聚合开发、测试、文档、发布、素材、调研等任务类型的消耗 |
| 数据源可信度 | `codex-probe confidence-report` | 展示来源、字段覆盖、缺失字段、置信上限和为什么不能更精确 |
| 单会话详情 | `codex-probe session-report <session_id>` | 查看时间线、快照和高消耗区间 |
| 总账报告 | `codex-probe ledger-report --range 30d` | 汇总 token、credits、项目和建议 |
| 本地 Dashboard | `codex-probe dashboard` | 生成可打开的本地 HTML 页面 |
| Dashboard 筛选 | 本地 HTML 内置 | 按项目、开始日期、结束日期、置信度、模型过滤 |
| Watcher 状态页 | `codex-probe watch status-page` | 生成友好的本地 watcher 状态页 |
| 脱敏样本采集 | `codex-probe samples collect-rollout` | 输出只含白名单字段和哈希的校准样本 |
| 轻量安装说明 | [docs/INSTALL.md](docs/INSTALL.md) | Codex 桌面版、仓库脚本、uvx、pipx 和 Homebrew Formula 草案 |
| 状态栏 App 文档 | [docs/MACOS_MENUBAR_APP.md](docs/MACOS_MENUBAR_APP.md) | 构建、配置、使用和隐私边界 |
| 隐私审计 | `codex-probe privacy inspect` | 查看启用数据源、读取字段和审计日志 |
| 删除 watcher | `codex-probe delete --watcher --yes` | 删除 watcher 状态、lock、stop flag 和日志 |
| 删除账本 | `codex-probe delete --ledger --yes` | 删除账本业务数据，保留不含敏感原文的审计日志 |

置信度分为：

- `exact`：用户显式提供的官方导出或等价结构化数据直接提供会话 ID 和 token 字段。
- `high`：本地结构化记录能稳定关联到会话和 token 字段，但仍不是官方账单。
- `medium`：存在多会话或时间窗口重叠，只能按元信息估算。
- `low`：只有全局额度变化，不能当作精确账单。

`credits` 的口径更谨慎：

- 它表示数据源提供的 credits / cost / quota 数值，不等同于美元、人民币或官方账单金额。
- `credits delta` 只在同一来源同一口径可解释为消耗差值时展示；无法确认口径时显示为 `未知`。
- 会话排行中的开始/结束时间按当前系统时区显示。例如中国大陆系统会显示为 `UTC+08:00`。

## 三分钟跑通示例

```bash
mkdir -p .probe reports/ledger

codex-probe --db .probe/setup-demo.db setup --demo
```

如果你想拆开跑：

```bash
codex-probe --db .probe/ledger.db ledger init

codex-probe --db .probe/ledger.db sources doctor

codex-probe --db .probe/ledger.db sources doctor --deep

codex-probe --db .probe/ledger.db ledger import \
  --official-export examples/ledger-samples/official-export.csv

codex-probe --db .probe/ledger.db ledger inspect-export \
  examples/ledger-samples/official-export.jsonl

codex-probe --db .probe/ledger.db ledger import \
  --official-export examples/ledger-samples/official-export.jsonl

codex-probe --db .probe/ledger.db ledger import-history \
  --dry-run \
  --source local-codex \
  --root examples/ledger-samples/local-codex

codex-probe --db .probe/ledger.db ledger import-history \
  --source local-codex \
  --root examples/ledger-samples/local-codex

codex-probe --db .probe/ledger.db watch once \
  --root examples/ledger-samples/local-codex

codex-probe --db .probe/ledger.db ledger import \
  --snapshot examples/ledger-samples/snapshot-delta.json

codex-probe --db .probe/ledger.db sessions \
  --range 7d \
  --out reports/ledger/sessions.md

codex-probe --db .probe/ledger.db session-report \
  session_readme_release \
  --out reports/ledger/session-readme-release.md

codex-probe --db .probe/ledger.db ledger-report \
  --range 30d \
  --out reports/ledger/ledger-report.md

codex-probe --db .probe/ledger.db projects \
  --range 30d \
  --out reports/ledger/project-summary.md

codex-probe --db .probe/ledger.db weekly-report \
  --range 30d \
  --out reports/ledger/weekly-report.md

codex-probe --db .probe/ledger.db timeline \
  --range 30d \
  --out reports/ledger/timeline.md

codex-probe --db .probe/ledger.db alerts \
  --range 30d \
  --out reports/ledger/alerts.md

codex-probe --db .probe/ledger.db confidence-report \
  --out reports/ledger/source-confidence.md

codex-probe --db .probe/ledger.db task-report \
  --range 30d \
  --out reports/ledger/task-report.md

codex-probe --db .probe/ledger.db dashboard \
  --range 7d \
  --out reports/ledger/dashboard.html

codex-probe --db .probe/ledger.db watch status-page \
  --out reports/ledger/watch-status.html

codex-probe --db .probe/ledger.db privacy inspect \
  --out reports/ledger/privacy-report.md
```

删除本地账本业务数据：

```bash
codex-probe --db .probe/ledger.db delete --ledger --yes
codex-probe --db .probe/ledger.db delete --watcher --yes
```

## 时间范围

会话账本不写死最近 7 天。支持：

```bash
codex-probe sessions --range today
codex-probe sessions --range yesterday
codex-probe sessions --since 24h
codex-probe sessions --range 3d
codex-probe sessions --range 7d
codex-probe sessions --range 30d
codex-probe sessions --from 2026-06-01 --to 2026-06-23
```

## 示例数据

| 文件 | 用途 |
|---|---|
| `examples/ledger-samples/official-export.csv` | 脱敏官方导出样本，覆盖 exact 置信度 |
| `examples/ledger-samples/official-export.json` | 脱敏官方 JSON 导出样本 |
| `examples/ledger-samples/official-export.jsonl` | 脱敏官方 JSONL 导出样本 |
| `examples/ledger-samples/official-export-alt.json` | 字段名不标准的导出样本 |
| `examples/ledger-samples/official-export-alt.mapping.json` | 字段映射样本 |
| `examples/ledger-samples/snapshot-delta.json` | 脱敏快照样本，覆盖 high / medium / low 置信度 |
| `examples/ledger-samples/local-status-snapshots.json` | local_status allowlist 示例 |
| `examples/ledger-samples/local-codex/` | synthetic Codex rollout 样本，用于验证本地历史导入 |
| `examples/ledger-samples/local-codex-variants/` | synthetic Codex rollout 变体样本，覆盖字段别名、缺失模型、多项目和多会话 |
| `examples/ledger-samples/local-codex-stress/` | synthetic Codex rollout 压力样本，覆盖重复快照、多会话重叠、异常时间戳和缺失字段 |
| `examples/reports/ledger/` | v0.9.0 会话账本、阶段时间线、预警、可信度、任务归因、项目汇总和周报示例报告 |
| `examples/status-samples/` | 旧版 `/status` 样本库 |
| `examples/risky-skill.md` | Skill / 输出质量体检风险样例 |

所有示例均应是脱敏样本，不包含真实 cookie、token、邮箱、手机号或用户私密路径。

收集真实脱敏 rollout 校准样本：

```bash
codex-probe --db .probe/probe.db samples collect-rollout \
  --out reports/ledger/redacted-rollout-samples.jsonl \
  --limit-files 40 \
  --max-records 80
```

输出只包含 token 用量白名单字段和哈希，不包含聊天正文、prompt、assistant 输出、cookie、token 或完整路径。

## Codex 桌面版怎么用

最友好的方式，是在 **Codex 桌面版 App** 中打开这个仓库目录，然后按场景复制下面的提示词。

### 只跑安全 demo

```text
请运行 scripts/setup-local.sh，只使用仓库 demo 样本生成 Codex 用量 Dashboard。

要求：
1. 如果还没安装，请在本项目里创建本地虚拟环境并安装。
2. 只使用仓库 examples/ledger-samples/ 里的 demo 样本。
3. 生成 reports/ledger/dashboard.html、sessions.md、ledger-report.md、project-summary.md、weekly-report.md、timeline.md、alerts.md、source-confidence.md、task-report.md、privacy-report.md 和 watch-status.html。
4. 最后告诉我 Dashboard 和报告路径，以及示例里哪个会话最贵。
5. 不要读取我的真实 Codex 历史、浏览器 cookie、token、钥匙串、系统凭据或聊天正文。
6. 不要上传任何数据。
```

### 分析自己的本地 Codex 会话

```text
请用 BLCaptain Codex Probe CLI 分析我本地 Codex 最近 7 天的会话 token 用量。

要求：
1. 如果还没安装，请在本项目里创建本地虚拟环境并安装。
2. 先运行 dry-run 检查可用数据源，不要直接导入未知内容。
3. 只读取 Codex rollout JSONL 中的 token 用量白名单字段。
4. 如果 dry-run 显示有可导入 token 记录，再导入本地历史。
5. 生成 reports/ledger/sessions.md、ledger-report.md、project-summary.md、weekly-report.md、timeline.md、alerts.md、source-confidence.md、task-report.md、privacy-report.md、dashboard.html 和 watch-status.html。
6. 用普通话告诉我：哪个会话最贵、哪个项目最贵、哪段时间增长最快、主要消耗在哪类任务、置信度是什么、为什么贵、怎么降配、什么时候该停。
7. 明确说明：credits 不等同于美元、人民币或官方账单金额；置信度和建议只是治理参考。
8. 不要读取聊天正文、prompt、assistant 输出、浏览器 cookie、token、钥匙串、系统凭据或完整私密路径。
9. 不要上传任何数据。
```

### 只分析一次 `/status`

```text
我会粘贴 Codex /status，请用 BLCaptain Codex Probe CLI 做一次本地用量体检。

要求：
1. 先脱敏明显的 key、cookie、token、邮箱、手机号和会话标识。
2. 保存为 .probe/my-status.txt。
3. 生成 reports/my-usage-report.md。
4. 用普通话解释：为什么贵、怎么降配、什么时候该停。
5. 明确建议动作：继续、降配还是停止。
6. 只处理我显式提供的文本，不读取浏览器 cookie、token、钥匙串、系统凭据或私密目录。
7. 不上传任何数据。

这是我的 /status：
[把 /status 文本粘贴在这里]
```

更多可复制提示词见 [Codex 桌面版提示词](docs/CODEX_DESKTOP_PROMPT.md)。

## 保留能力：`/status` 用量体检

如果你只想分析一次 `/status`，仍然可以使用：

```bash
codex-probe --db .probe/demo.db doctor \
  --status examples/status-codex-desktop.txt \
  --skill examples/risky-skill.md \
  --budget-tokens 100000 \
  --out-dir reports/doctor
```

或者只生成用量报告：

```bash
codex-probe --db .probe/demo.db import \
  --status examples/status-codex-desktop.txt \
  --goal "生成交付报告"

codex-probe --db .probe/demo.db usage-report \
  --budget-tokens 100000 \
  --out reports/usage-report.md
```

## 保留能力：Skill / 输出质量体检

```bash
codex-probe --db .probe/demo.db skill-lint \
  examples/risky-skill.md \
  --out reports/skill-lint-report.md
```

体检会检查：

- AI 味和模板化表达。
- 自动安装插件或连接器。
- 绕登录、共享账号、拼车、规避计费、绕额度等风险表达。
- 代理、拦截、抓包或修改 Codex / OpenAI 请求。
- 默认外传、上传到第三方服务器或 webhook。
- 伪装真人、冒充身份或绕过平台风控。
- 保证省钱、100% 准确、永久免费等过度承诺。
- 缺失验收标准。
- 缺失隐私和删除边界。
- API key、cookie、token、邮箱或手机号等敏感信息。

## 数据与隐私

- 不登录 OpenAI 或 Codex。
- 不读取浏览器 cookie、token、钥匙串或系统凭据。
- 不代理、拦截或修改 Codex 请求。
- 不读取聊天正文。
- 不上传数据到云端。
- 默认不后台采集，`watch start` 或 macOS LaunchAgent 必须由用户显式执行。
- local history 只读取 Codex rollout JSONL 中的 token 用量白名单字段；跳过聊天正文、prompt、assistant 输出和工具参数。
- 完整私密路径默认不展示，只保留哈希。
- `dashboard` 生成本地 HTML 文件，不启动云端服务。
- `delete --ledger --yes` 会删除账本业务数据，并保留不含敏感原文的审计日志。
- `delete --watcher --yes` 会删除 watcher 状态、日志和控制文件。
- 不承诺省钱、不承诺无限额度、不替代官方 dashboard 或账单。

详见 [隐私与安全说明](docs/PRIVACY_SECURITY.md)。

## 本地命令

自动化测试：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

语法检查：

```bash
python3 -m compileall src tests scripts/run_acceptance.py
```

端到端验收：

```bash
python3 scripts/run_acceptance.py
```

验收脚本只写入本地临时验收产物；这些产物已被 `.gitignore` 忽略，不应提交到 GitHub。

## 目录结构

```text
BLCaptain-Codex-Probe-CLI/
├── assets/screenshots/               # README 工作截图
├── examples/ledger-samples/          # 会话账本脱敏样本
├── examples/reports/ledger/          # 会话账本示例报告
├── README.md                         # 中文说明
├── README.en.md                      # English README
├── CHANGELOG.md                      # 版本更新记录
├── LICENSE                           # MIT License
├── pyproject.toml                    # Python 包与 CLI 入口
├── docs/
│   ├── CODEX_DESKTOP_PROMPT.md       # Codex 桌面版提示词
│   ├── INSTALL.md                     # 轻量安装方式
│   ├── MACOS_MENUBAR_APP.md          # macOS 状态栏 App 本地体验版
│   ├── MACOS_RELEASE_DISTRIBUTION.md # macOS App 正式分发边界
│   ├── MACOS_WATCHER.md              # macOS LaunchAgent watcher 入口
│   ├── PRIVACY_SECURITY.md           # 隐私与安全边界
│   └── SAMPLE_COLLECTION.md          # 脱敏样本采集说明
├── scripts/
│   ├── macos/                        # macOS LaunchAgent 安装/卸载脚本
│   └── run_acceptance.py             # 端到端验收脚本
├── src/codex_usage_skill_probe/       # CLI 源码
└── tests/                            # 单元测试与端到端测试
```

## 发布验收标准

发布 v0.9.0 前必须满足：

- 可以从干净环境 `python -m pip install .` 安装。
- `codex-probe --version` 返回 `0.9.0`。
- 能导入官方导出 CSV / JSON / JSONL、mapping 样本、本地历史 synthetic rollout 和快照样本。
- 能跑通 `sources doctor --deep`、`ledger inspect-export`、`ledger map-export`、`ledger import-history --dry-run`。
- 能跑通 `setup --demo`、`watch once/start/status/logs/stop/status-page` 和 `delete --watcher --yes`。
- 能输出会话排行、单会话报告、总账报告、阶段级时间线、本地预算预警、任务类型归因、数据源可信度、隐私审计报告、本地 HTML Dashboard 和 watcher 状态页。
- 能输出项目级汇总报告和 Codex 周报。
- macOS 状态栏 App 可以 `swift build`，并可通过脚本打包为 `build/CodexProbeBar.app`。
- 状态栏 App 复用 CLI JSON 输出，不直接读取 cookie、token、钥匙串、聊天正文或网络请求。
- Dashboard 支持按项目、日期、置信度和模型筛选。
- Dashboard 首屏包含今日、本周、高风险会话、该停会话、预算预警、数据源可信度和任务类型归因。
- 能生成只含白名单字段和哈希的脱敏 rollout 校准样本。
- 样本库覆盖 rollout 字段别名、缺失模型、缺项目路径、缺上下文窗口、异常时间戳、重复快照、多项目和多会话场景。
- JSON / HTML 报告契约测试覆盖 sessions、ledger、project summary、weekly report、timeline、alerts、task report、confidence report、privacy report 和 dashboard。
- Skill 体检规则覆盖自动安装、绕登录/计费、外传数据、请求拦截、伪装真人和过度承诺。
- 安装文档包含 Codex 桌面版、仓库脚本、uvx、pipx 和 Homebrew Formula 草案。
- 菜单栏 App / 桌面组件评估说明不读取登录态的产品路径。
- 每条会话都有数据源和 `exact/high/medium/low` 置信度。
- 能删除本地账本业务数据。
- 报告不泄露完整 API key、cookie、token、邮箱、手机号或用户私密路径。
- README、英文 README、CHANGELOG、CI、隐私说明和发布清单齐全。

## Roadmap

- 持续收集更多真实脱敏 rollout 样本，校准不同 Codex 版本的数据结构。
- 正式发布 PyPI 包，并在验证后发布 Homebrew tap。
- 根据用户反馈决定是否实现极薄 macOS 菜单栏 App。
- 增加更细的趋势图、阈值配置文件和可导出的 Dashboard JSON schema。

## FAQ

**Q：它是 Codex Skill 吗？**

A：不是。它是 CLI。它可以检查 Skill 或输出文本，但本身不是给 Agent 读取的 Skill 指令包。

**Q：它需要 OpenAI API Key 吗？**

A：不需要。它只分析用户显式提供的本地文件和示例数据。

**Q：它能自动读取我的历史会话 token 吗？**

A：如果你的本机 Codex 结构化 rollout 日志包含 token 用量字段，可以用 `ledger import-history --source local-codex` 本地导入。它只读取白名单字段，不读取聊天正文、prompt、assistant 输出、cookie、token、钥匙串或系统凭据。如果日志里没有 token 字段，它不会伪造用量。

**Q：它能直接读取我的官方账单吗？**

A：不能直接登录读取。它支持用户显式提供的官方导出文件，也支持本地 Codex 结构化日志里的 token 字段；不读取登录态、浏览器 cookie 或官方后台隐藏数据。

**Q：它能精确知道每条真实会话的 token 吗？**

A：只有数据源本身直接提供会话 ID 和 token 字段时才接近 `exact`。本地 rollout 即使能稳定解析，也标为 `high`，因为它不是官方账单。快照和全局额度变化会标注为 `medium` 或 `low`，不能当作精确账单。

**Q：它能保证省钱吗？**

A：不能。它只能定位消耗、解释风险、按阈值给出降配和停止建议，最终仍要由你判断。

**Q：它会保存我的数据吗？**

A：只保存到你指定的本地 SQLite 文件。你可以用 `delete --ledger --yes` 删除账本业务数据，也可以用 `delete --all --yes` 删除旧版业务数据。

## 关于作者

由 **爆裂队长NEXT（BLCaptain）** 独立创作与维护。

- GitHub：[@dososo](https://github.com/dososo)
- X / Twitter：[@thinkszyg](https://x.com/thinkszyg)
- 邮箱：[blteam2026@outlook.com](mailto:blteam2026@outlook.com)
- 开源中国传统纹样图录项目维护者：[wenyang.net](https://wenyang.net)

如果这个项目对你有帮助，欢迎 Star、分享，或在 X 上 @我交流。

## License

MIT License. See [LICENSE](LICENSE).
