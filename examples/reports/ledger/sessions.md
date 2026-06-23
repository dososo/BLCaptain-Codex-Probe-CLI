# Codex 会话级 Token 账本

时间范围：7d

| 会话 | 项目 | token delta | credits delta | 上下文峰值 | 置信度 | 数据源 | 建议 |
|---|---|---:|---:|---:|---|---|---|
| README 发布准备 | Codex Probe CLI | 142047 | 18.42 | 55.06 | exact | official_export | 停止当前长会话，保存成果后拆到新会话 |
| 小红书素材生成 | Codex Probe CLI | 61320 | 7.80 | 23.77 | exact | official_export | 降配或拆分后续任务，避免继续放大上下文 |
| Skill 优化验收 | BLCaptain Skills | 38900 | 4.90 | 15.08 | exact | official_export | 可以继续，但保留停止线 |
| CI 修复会话 | Codex Probe CLI | 22400 | 2.44 | 13.33 | high | snapshot_delta | 可以继续，但保留停止线 |
| 竞品调研会话 | Codex Research | 18200 | 1.80 | 10.54 | medium | snapshot_delta | 可以继续，但保留停止线 |
| 未知全局额度变化 | 未归属项目 | 6400 | 0.50 | 9.00 | low | snapshot_delta | 可以继续，但保留停止线 |

## 说明

- `exact` 表示官方导出或等价结构化数据直接提供会话级用量。
- `high` 表示同一会话快照可计算 delta。
- `medium` 表示存在多会话或窗口重叠，只能按可见元信息归因。
- `low` 只能作为估算，不能当作精确账单。
