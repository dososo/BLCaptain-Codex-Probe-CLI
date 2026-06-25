# Codex 任务级用量自查报告

定位：Watch / 验证型探针。本报告只解释用户显式提供的本地数据，不替代官方 usage dashboard 或 `/status`。

## 决策卡片

| 问题 | 结论 |
|---|---|
| 建议动作 | **停止** |
| 为什么贵 | 当前任务已累计 142,047 tokens，上下文规模已经偏大；会话上下文只剩 45% |
| 怎么降配 | 开新会话时只带最终 README、目标仓库路径、最新 commit 和必要错误日志；不要默认重读全项目，先点名必要文件；把发布准备、CI 修复、README 微调拆成独立小任务。 |
| 什么时候该停 | 现在就停止扩展范围，只保留保存成果、提交、推送和必要验证。 |

## 任务摘要

| 字段 | 值 |
|---|---|
| task_id | `task_44f2638fed60` |
| model | 未知 |
| mode | 未知 |
| input_tokens | 未知 |
| output_tokens | 未知 |
| cached_input_tokens | 未知 |
| total_tokens | 142047 |
| credits | 未知 |
| context_remaining_percent | 45.0 |
| context_used_tokens | 142047 |
| context_limit_tokens | 258000 |
| five_hour_remaining_percent | 94.0 |
| five_hour_reset | 18:51 |
| seven_day_remaining_percent | 72.0 |
| seven_day_reset | 6月25日 |
| quota_remaining | 45.0 |
| quota_limit | 100.0 |

## 风险与建议

| 标签 | 严重度 | 置信度 | 证据 | 建议 | 证据来源 |
|---|---|---:|---|---|---|
| `OVER_BUDGET` | high | 0.94 | total_tokens=142047 超过 budget_tokens=100000 | 停止继续扩大上下文；拆分任务；优先复用缓存输入；下一轮改用更小模型或降低推理强度。 | E-011,E-012,E-013 |

## 停止线

- 如果报告只出现 `LOW_CONFIDENCE_USAGE`，不要据此做强决策，先补充更完整的 `/status` 或手工数据。
- 如果出现 `OVER_BUDGET`、`CREDITS_OVER_BUDGET` 或 `STOP_RECOMMENDED`，先停止扩展任务，保存成果，再决定是否拆分、降配或继续。
- 本工具不承诺省钱、额度翻倍、绕过限制或替代官方用量系统。
