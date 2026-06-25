# Codex 数据源可信度报告

定位：解释每个数据源能支持多精细的 token 归因，以及为什么有些字段不能更精确。

| 数据源 | 启用 | 置信上限 | 会话数 | 快照数 | 已有字段 | 缺失字段 | 诊断 |
|---|---|---|---:|---:|---|---|---|
| desktop_visible | False | medium | 0 | 0 | 无 | session_id, total_tokens, credits, context_window, context_state, model, project | 已登记数据源，但当前账本没有该来源快照；无法做会话级归因。 |
| local_codex_rollout | True | high | 6 | 10 | session_id, total_tokens, context_window, model, project | credits, context_state | 本地 rollout 只读取 token 白名单字段；schema 变动时可能出现缺字段。 |
| local_status | False | high | 0 | 0 | 无 | session_id, total_tokens, credits, context_window, context_state, model, project | 已登记数据源，但当前账本没有该来源快照；无法做会话级归因。 |
| official_export | True | exact | 6 | 6 | session_id, total_tokens, credits, context_window, context_state, model, project | 无 | 字段覆盖完整，可用于当前来源口径下的高质量归因。 |
| snapshot_delta | True | high | 3 | 5 | session_id, total_tokens, credits, context_window, context_state, model, project | 无 | 字段覆盖完整，可用于当前来源口径下的高质量归因。 |

## 口径说明

- `official_export`：用户显式提供的官方或等价结构化导出，若含会话级 token 字段，置信上限可到 `exact`。
- `local_codex_rollout`：本地结构化 rollout token 字段，置信上限通常为 `high`，不是官方账单。
- `snapshot_delta`：用户显式提供或本地快照推导的 delta，置信度取决于是否能稳定关联会话和时间窗口。
- 如果缺少 `total_tokens`、模型、项目或上下文窗口，本工具会显示缺失，不会补造。

## 隐私边界

- 不登录 OpenAI，不读取浏览器 cookie、OpenAI token、钥匙串或系统凭据。
- 不抓包、不代理、不拦截请求、不读取聊天正文。
- 所有报告均基于本地用户显式提供或本机可见的结构化用量字段。
