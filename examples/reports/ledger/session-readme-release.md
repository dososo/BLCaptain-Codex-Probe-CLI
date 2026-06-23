# Codex 单会话用量详情

| 字段 | 值 |
|---|---|
| 会话 | README 发布准备 |
| session_id | `session_readme_release` |
| 项目 | Codex Probe CLI |
| 开始时间 | 2026-06-22T09:00:00+00:00 |
| 结束时间 | 2026-06-22T11:10:00+00:00 |
| token delta | 142047 |
| credits delta | 18.42 |
| 上下文峰值 | 55.06 |
| 数据源 | official_export |
| 置信度 | exact (0.99) |
| 建议 | 停止当前长会话，保存成果后拆到新会话 |
| 证据 | 官方导出直接提供会话级用量字段 |

## 时间线

| 时间 | total_tokens | credits | context_used | context_limit | context_remaining | 数据源 |
|---|---:|---:|---:|---:|---:|---|
| 2026-06-22T11:10:00+00:00 | 142047 | 18.42 | 142047 | 258000 | 未知 | official_export |

## 高消耗区间

| 开始 | 结束 | token delta | credits delta | 判断 |
|---|---|---:|---:|---|
| 2026-06-22T09:00:00+00:00 | 2026-06-22T11:10:00+00:00 | 142047 | 18.42 | 高消耗区间 |

## 高消耗判断

- 该会话 token delta 超过 100,000，属于高消耗会话；建议停止当前长会话，开新会话只带必要上下文。

## 隐私边界

- 本报告只展示会话元信息和 token/credits 数字。
- 不包含聊天正文、浏览器 cookie、OpenAI token、系统凭据或完整私密路径。
