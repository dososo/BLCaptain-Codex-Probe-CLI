# Codex Ledger 隐私审计报告

## 数据源

| 类型 | 是否启用 | 置信度上限 | 授权范围 |
|---|---|---|---|
| desktop_visible | False | medium | 需要用户显式授予系统可访问性权限 |
| local_status | False | high | 预留 allowlist 字段读取，不扫描私密目录 |
| official_export | True | exact | 用户显式提供的官方导出 CSV/JSON；不读取浏览器、cookie、token 或聊天正文。 |
| snapshot_delta | True | high | 用户显式提供的本地快照文件；只读取会话元信息和 token 数字。 |

## 审计日志

| 时间 | 动作 | 摘要 |
|---|---|---|
| 2026-06-23T11:57:11+00:00 | source_upserted | {"confidence_ceiling": "exact", "enabled": false, "source_type": "official_export"} |
| 2026-06-23T11:57:11+00:00 | source_upserted | {"confidence_ceiling": "high", "enabled": false, "source_type": "snapshot_delta"} |
| 2026-06-23T11:57:11+00:00 | source_upserted | {"confidence_ceiling": "high", "enabled": false, "source_type": "local_status"} |
| 2026-06-23T11:57:11+00:00 | source_upserted | {"confidence_ceiling": "medium", "enabled": false, "source_type": "desktop_visible"} |
| 2026-06-23T11:57:11+00:00 | ledger_initialized | {"db_name": "codex-probe-v040-example-ledger-interval-23383.db", "source_count": 4} |
| 2026-06-23T11:57:11+00:00 | source_upserted | {"confidence_ceiling": "exact", "enabled": true, "source_type": "official_export"} |
| 2026-06-23T11:57:11+00:00 | official_export_imported | {"filename": "official-export.csv", "sessions": 3, "snapshots": 3} |
| 2026-06-23T11:57:11+00:00 | source_upserted | {"confidence_ceiling": "high", "enabled": true, "source_type": "snapshot_delta"} |
| 2026-06-23T11:57:11+00:00 | snapshot_delta_imported | {"filename": "snapshot-delta.json", "snapshots": 5} |

## 明确不读取

- 浏览器 cookie
- OpenAI token
- 钥匙串和系统凭据
- 聊天正文
- 完整私密路径
