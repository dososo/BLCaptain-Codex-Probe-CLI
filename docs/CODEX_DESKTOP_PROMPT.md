# Codex 桌面版提示词

复制下面的提示词到 Codex 桌面版 App。适合你已经打开本仓库目录，并希望 Codex 自动调用本地 CLI 完成会话级账本分析、`/status` 用量体检或 Skill / 输出质量体检。

## 安装这个仓库并体验

```text
帮我安装这个仓库：https://github.com/dososo/BLCaptain-Codex-Probe-CLI

要求：
1. 克隆仓库后进入项目目录。
2. 运行 scripts/setup-local.sh。
3. 安装完成后先使用仓库 examples/ledger-samples/ 里的示例数据生成 Dashboard。
4. 生成 reports/ledger/dashboard.html、sessions.md、ledger-report.md、project-summary.md、weekly-report.md、timeline.md、alerts.md、source-confidence.md、task-report.md、privacy-report.md 和 watch-status.html。
5. 最后告诉我 Dashboard 和报告路径，以及示例里哪个会话最贵。
6. 不要读取我的真实 Codex 历史、浏览器 cookie、token、钥匙串、系统凭据或聊天正文。
7. 不要上传任何数据。
```

## 构建 macOS 状态栏 App

```text
请帮我构建并启动 BLCaptain Codex Probe Bar 这个 macOS 状态栏 App。

要求：
1. 先确认本仓库 CLI 已安装；如果没有，请运行 scripts/setup-local.sh。
2. 运行 scripts/macos/build-codex-probe-bar.sh。
3. 打开 build/CodexProbeBar.app。
4. 告诉我状态栏 App 的配置、报告目录和 Dashboard 路径。
5. 不要读取浏览器 cookie、token、钥匙串、系统凭据或聊天正文。
6. 不要上传任何数据。
```

## 使用仓库示例数据

```text
请运行 scripts/setup-local.sh，只使用仓库示例样本生成 Codex 用量 Dashboard。

要求：
1. 如果还没安装，请在本项目里创建本地虚拟环境并安装。
2. 只使用仓库 examples/ledger-samples/ 里的示例样本。
3. 生成 reports/ledger/dashboard.html、sessions.md、ledger-report.md、project-summary.md、weekly-report.md、timeline.md、alerts.md、source-confidence.md、task-report.md、privacy-report.md 和 watch-status.html。
4. 最后告诉我 Dashboard 和报告路径，以及示例里哪个会话最贵。
5. 不要读取我的真实 Codex 历史、浏览器 cookie、token、钥匙串、系统凭据或聊天正文。
6. 不要上传任何数据。
```

## 自动检查本地 Codex token 会话账本

```text
请用 BLCaptain Codex Probe CLI 分析我本地 Codex 最近 7 天的会话 token 用量。

目标：
1. 如果还没安装，请在本项目里创建本地虚拟环境并安装。
2. 运行安全数据源检查：codex-probe sources doctor --deep。
3. 先 dry-run：codex-probe ledger import-history --dry-run --source local-codex。
4. 如果 dry-run 显示有可导入 token 记录，再执行：codex-probe ledger import-history --source local-codex。
5. 生成：
   - reports/ledger/sessions.md
   - reports/ledger/ledger-report.md
   - reports/ledger/project-summary.md
   - reports/ledger/weekly-report.md
   - reports/ledger/timeline.md
   - reports/ledger/alerts.md
   - reports/ledger/source-confidence.md
   - reports/ledger/task-report.md
   - reports/ledger/privacy-report.md
   - reports/ledger/dashboard.html
   - reports/ledger/watch-status.html
6. 用普通话解释：哪个会话最贵、哪个项目最贵、哪段时间增长最快、主要消耗在哪类任务、发生在哪个本机时区时间段、credits 代表什么、数据源是什么、置信度是什么、建议继续/降配/停止。
7. 明确说明：credits 不等同于美元、人民币或官方账单金额；置信度和建议是治理参考，不替代官方 dashboard。

边界：
- 只读取 Codex rollout JSONL 中的 token 用量白名单字段。
- 不读取浏览器 cookie、token、钥匙串、系统凭据、聊天正文、prompt、assistant 输出或工具参数。
- 不输出完整私密路径，只能展示哈希或脱敏摘要。
- 不抓包，不代理，不修改 Codex 请求。
- 不上传任何数据。
- 不承诺省钱、无限额度或额度提升。
```

## 分析自己的 `/status`

```text
请用 BLCaptain Codex Probe CLI 分析我下面提供的 Codex /status。

目标：
1. 先脱敏明显的 key、cookie、token、邮箱、手机号和会话标识。
2. 保存为 .probe/my-status.txt。
3. 用 codex-probe doctor 或 usage-report 生成任务级用量报告。
4. 报告放到 reports/my-usage-report.md 或 reports/doctor/。
5. 用普通话解释：为什么贵、怎么降配、什么时候该停。
6. 明确建议动作：继续、降配还是停止。

边界：
- 只处理我显式提供的文本。
- 不读取浏览器、登录态、cookie、token、钥匙串、系统凭据或私密目录。
- 不上传任何数据。
- 不承诺省钱、无限额度或额度提升。

这是我的 /status：
[把 /status 文本粘贴在这里]
```

## 跑示例数据

```text
请用 BLCaptain Codex Probe CLI 跑一次本地示例：

1. 如果还没安装，请在本项目里创建本地虚拟环境并安装。
2. 使用 examples/ledger-samples/official-export.csv、examples/ledger-samples/snapshot-delta.json、examples/ledger-samples/local-codex-variants/ 和 examples/ledger-samples/local-codex-stress/ 跑会话级账本、阶段时间线、预算预警、数据源可信度、任务归因、项目汇总和周报。
3. 使用 examples/status-codex-desktop.txt 和 examples/risky-skill.md 跑 codex-probe doctor。
4. 报告放到 reports/ledger/ 和 reports/doctor/。
5. 删除本地业务数据后确认再次生成旧版用量报告返回 NO_USAGE_DATA。
6. 最后告诉我报告路径、主要风险、建议继续、降配还是停止。

不要上传任何数据，不要读取浏览器 cookie、token、钥匙串、系统凭据或聊天正文。
```

## 体检自己的 Skill 或输出

```text
请用 BLCaptain Codex Probe CLI 体检我下面提供的 Skill / 提示词 / AI 输出。

目标：
1. 先脱敏明显的 key、cookie、token、邮箱、手机号和会话标识。
2. 保存为 .probe/my-skill-or-output.md。
3. 用 codex-probe skill-lint 生成质量体检报告。
4. 报告放到 reports/my-skill-lint-report.md。
5. 总结 AI 味、插件风险、敏感信息、缺失验收和隐私边界问题。

边界：
- 只处理我显式提供的文本。
- 不读取浏览器、登录态、cookie、token、钥匙串、系统凭据或私密目录。
- 不自动安装、启用或推荐插件。
- 不承诺平台过审或真人伪装。

这是我的材料：
[把文本粘贴在这里]
```
