# Codex 桌面版提示词

复制下面的提示词到 Codex 桌面版 App。适合你已经打开本仓库目录，并希望 Codex 自动调用本地 CLI 完成分析。

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
2. 使用 examples/status-codex-desktop.txt 和 examples/risky-skill.md 跑 codex-probe doctor。
3. 报告放到 reports/doctor/。
4. 删除本地业务数据后确认再次生成报告返回 NO_USAGE_DATA。
5. 最后告诉我 doctor 报告路径、主要风险、建议继续、降配还是停止。

不要上传任何数据，不要读取浏览器 cookie、token 或系统凭据。
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
