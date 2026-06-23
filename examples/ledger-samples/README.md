# Ledger 样本库

这些样本用于验证 BLCaptain Codex Probe CLI v0.4.0 的会话级 Token 账本能力。

所有数据均为合成或脱敏样本，不包含真实会话 ID、cookie、token、邮箱、手机号或本地用户路径。

| 文件 | 数据源 | 覆盖 |
|---|---|---|
| `official-export.csv` | 用户显式提供的官方导出 | `exact` 置信度，会话级 token/credits |
| `snapshot-delta.json` | 用户显式提供的本地快照 | `high`、`medium`、`low` 置信度 |
| `local-status-snapshots.json` | allowlist 状态样本 | Source Doctor 探测和 `high` fallback |

核心验证问题：

1. 哪个 Codex 会话消耗最多？
2. 哪个项目消耗最多？
3. 哪个时间段 token delta 增长最快？
4. 每条结论的数据源和置信度是什么？
