# Codex 桌面版提示词

复制下面的提示词到 Codex 桌面版 App。适合你已经打开本仓库目录，并希望 Codex 自动调用本地 CLI 完成会话级账本分析、`/status` 用量体检或 Skill / 输出质量体检。

## 自动检查本地 Codex token 会话账本

```text
请用 BLCaptain Codex Probe CLI 自动检查本地 Codex token 会话账本，导入可用历史记录，分析最近 7 天哪个会话消耗最多，并生成报告。

目标：
1. 如果还没安装，请在本项目里创建本地虚拟环境并安装。
2. 初始化本地账本：codex-probe ledger init。
3. 运行安全数据源检查：codex-probe sources doctor --deep。
4. 先 dry-run：codex-probe ledger import-history --dry-run --source local-codex。
5. 如果 dry-run 显示有可导入 token 记录，再执行：codex-probe ledger import-history --source local-codex。
6. 同时验证官方导出适配：codex-probe ledger inspect-export examples/ledger-samples/official-export.jsonl。
7. 生成：
   - reports/ledger/sessions.md
   - reports/ledger/session-readme-release.md
   - reports/ledger/ledger-report.md
   - reports/ledger/privacy-report.md
   - reports/ledger/dashboard.html
8. 用普通话解释：哪个会话最贵、属于哪个项目、发生在哪个时间段、数据源是什么、置信度是什么、建议继续/降配/停止。

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
2. 使用 examples/ledger-samples/official-export.csv 和 examples/ledger-samples/snapshot-delta.json 跑会话级账本。
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
