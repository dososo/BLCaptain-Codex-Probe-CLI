# Ledger 样本库

这些样本用于验证 BLCaptain Codex Probe CLI v0.8.0 的会话级 Token 账本、阶段级时间线、预算预警、任务归因、数据源可信度、项目级聚合、周报、官方导出适配、本地历史导入和 watcher 能力。

所有数据均为合成或脱敏样本，不包含真实会话 ID、cookie、token、邮箱、手机号或本地用户路径。

公开示例统一使用 `gpt-5.5` 作为模型字段，便于 README 截图阅读。真实导入时，CLI 会原样展示数据源提供的模型名，不会猜测或强制改写。

| 文件 | 数据源 | 覆盖 |
|---|---|---|
| `official-export.csv` | 用户显式提供的官方导出 | `exact` 置信度，会话级 token/credits |
| `official-export.json` | 用户显式提供的官方 JSON 导出 | JSON 结构识别与导入 |
| `official-export.jsonl` | 用户显式提供的官方 JSONL 导出 | JSONL 结构识别与导入 |
| `official-export-alt.json` | 字段名不标准的导出 | 字段别名和 mapping |
| `official-export-alt.mapping.json` | 手工字段映射 | `ledger import --mapping` |
| `snapshot-delta.json` | 用户显式提供的本地快照 | `high`、`medium`、`low` 置信度 |
| `local-status-snapshots.json` | allowlist 状态样本 | Source Doctor 探测和 `high` fallback |
| `local-codex/` | synthetic Codex rollout JSONL | `ledger import-history` 和 `watch once` |
| `local-codex-variants/` | synthetic Codex rollout 变体 | 字段别名、缺失模型、多项目、多会话和不同 schema 校准 |
| `local-codex-stress/` | synthetic Codex rollout 压力样本 | 多会话重叠、重复快照、异常时间戳、缺失模型、缺项目路径和缺上下文窗口 |

核心验证问题：

1. 哪个 Codex 会话消耗最多？
2. 哪个项目消耗最多？
3. 哪个时间段 token delta 增长最快？
4. 每条结论的数据源和置信度是什么？
5. 当导出字段名不一致时，mapping 能否稳定导入？
6. 本地历史导入是否只读取 token 用量字段，并跳过正文？
7. 项目级汇总是否能找出最耗项目？
8. 周报是否能按本机时区归并到正确周？
9. 阶段级时间线是否能找出 token delta 增长最快的区间？
10. 本地预算预警是否能输出可执行的停止线？
11. 数据源可信度报告是否能解释字段缺失和精度边界？
