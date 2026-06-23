# Codex 会话级 Token 总账报告

定位：本地会话级账本。本报告只解释本地结构化账本数据，不替代官方 usage dashboard 或账单。

## 总览

| 字段 | 值 |
|---|---|
| 时间范围 | 30d |
| 会话数 | 10 |
| token delta | 436867 |
| credits delta | 40.46 |
| exact/high 置信会话 | 8 |
| 最耗会话 | README 发布准备 |

## 会话排行

| 排名 | 会话 | 项目 | token delta | credits delta | 置信度 | 数据源 | 建议 |
|---:|---|---|---:|---:|---|---|---|
| 1 | README 发布准备 | Codex Probe CLI | 142047 | 18.42 | exact | official_export | 停止当前长会话，保存成果后拆到新会话 |
| 2 | 小红书素材生成 | Codex Probe CLI | 61320 | 7.80 | exact | official_export | 降配或拆分后续任务，避免继续放大上下文 |
| 3 | Codex 会话 aa5b3c07 | 本地项目 7d72b21f626e8d0b | 58000 | 未知 | high | local_codex_rollout | 降配或拆分后续任务，避免继续放大上下文 |
| 4 | JSONL 发布验收 | codex-probe | 47400 | 2.40 | exact | official_export | 可以继续，但保留停止线 |
| 5 | Skill 优化验收 | BLCaptain Skills | 38900 | 4.90 | exact | official_export | 可以继续，但保留停止线 |
| 6 | 字段映射导入 | codex-probe | 36600 | 1.90 | exact | official_export | 可以继续，但保留停止线 |
| 7 | CI 修复会话 | Codex Probe CLI | 22400 | 2.44 | high | snapshot_delta | 可以继续，但保留停止线 |
| 8 | 竞品调研会话 | Codex Research | 18200 | 1.80 | medium | snapshot_delta | 可以继续，但保留停止线 |
| 9 | 未知全局额度变化 | 未归属项目 | 6400 | 0.50 | low | snapshot_delta | 可以继续，但保留停止线 |
| 10 | JSONL 轻量改文案 | codex-probe | 5600 | 0.30 | exact | official_export | 可以继续，但保留停止线 |

## 结论

最耗会话是「README 发布准备」，token delta 为 142,047。建议先停止该长会话，保存成果后拆到新会话。

## 隐私边界

- 本报告不包含聊天正文。
- 本报告不包含浏览器 cookie、OpenAI token、钥匙串、系统凭据或完整私密路径。
- 低置信归因只能作为估算，不应作为精确账单。
