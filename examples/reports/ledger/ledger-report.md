# Codex 会话级 Token 总账报告

定位：本地会话级账本。本报告只解释本地结构化账本数据，不替代官方 usage dashboard 或账单。

## 总览

| 字段 | 值 |
|---|---|
| 时间范围 | 30d |
| 会话数 | 6 |
| token delta | 289267 |
| credits delta | 35.86 |
| exact/high 置信会话 | 4 |
| 最耗会话 | README 发布准备 |

## 会话排行

| 排名 | 会话 | 项目 | token delta | credits delta | 置信度 | 数据源 | 建议 |
|---:|---|---|---:|---:|---|---|---|
| 1 | README 发布准备 | Codex Probe CLI | 142047 | 18.42 | exact | official_export | 停止当前长会话，保存成果后拆到新会话 |
| 2 | 小红书素材生成 | Codex Probe CLI | 61320 | 7.80 | exact | official_export | 降配或拆分后续任务，避免继续放大上下文 |
| 3 | Skill 优化验收 | BLCaptain Skills | 38900 | 4.90 | exact | official_export | 可以继续，但保留停止线 |
| 4 | CI 修复会话 | Codex Probe CLI | 22400 | 2.44 | high | snapshot_delta | 可以继续，但保留停止线 |
| 5 | 竞品调研会话 | Codex Research | 18200 | 1.80 | medium | snapshot_delta | 可以继续，但保留停止线 |
| 6 | 未知全局额度变化 | 未归属项目 | 6400 | 0.50 | low | snapshot_delta | 可以继续，但保留停止线 |

## 结论

最耗会话是「README 发布准备」，token delta 为 142,047。建议先停止该长会话，保存成果后拆到新会话。

## 隐私边界

- 本报告不包含聊天正文。
- 本报告不包含浏览器 cookie、OpenAI token、钥匙串、系统凭据或完整私密路径。
- 低置信归因只能作为估算，不应作为精确账单。
