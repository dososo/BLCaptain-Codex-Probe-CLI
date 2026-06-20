# Codex 任务级用量自查报告

定位：Watch / 验证型探针。本报告只解释用户显式提供的本地数据，不替代官方 usage dashboard 或 `/status`。

## 任务摘要

| 字段 | 值 |
|---|---|
| task_id | `task_4e81cd1cdbfa` |
| model | gpt-5.5 |
| mode | fast |
| input_tokens | 120000 |
| output_tokens | 22000 |
| cached_input_tokens | 60000 |
| total_tokens | 142000 |
| credits | 38.5 |
| quota_remaining | 12.0 |
| quota_limit | 100.0 |

## 风险与建议

| 标签 | 严重度 | 置信度 | 证据 | 建议 | 证据来源 |
|---|---|---:|---|---|---|
| `OVER_BUDGET` | high | 0.94 | total_tokens=142000 超过 budget_tokens=100000 | 停止继续扩大上下文；拆分任务；优先复用缓存输入；下一轮改用更小模型或降低推理强度。 | E-011,E-012,E-013 |
| `FAST_MODE_RISK` | medium | 0.78 | mode=fast | 除非任务确实需要速度或高推理，否则优先用普通模式或更小模型做初筛。 | E-013,R-002 |
| `STOP_RECOMMENDED` | high | 0.90 | quota_remaining=12.0，低于 quota_limit=100.0 的 15% | 建议停止非必要任务；只保留验证和保存成果动作。 | E-011,E-012 |

## 停止线

- 如果报告只出现 `LOW_CONFIDENCE_USAGE`，不要据此做强决策，先补充更完整的 `/status` 或手工数据。
- 如果出现 `OVER_BUDGET`、`CREDITS_OVER_BUDGET` 或 `STOP_RECOMMENDED`，先停止扩展任务，保存成果，再决定是否拆分、降配或继续。
- 本工具不承诺省钱、额度翻倍、绕过限制或替代官方用量系统。
