# Codex Ledger 隐私审计报告

## 数据源

| 类型 | 是否启用 | 置信度上限 | 授权范围 |
|---|---|---|---|
| desktop_visible | False | medium | 需要用户显式授予系统可访问性权限 |
| local_codex_rollout | True | high | 只读取 Codex rollout JSONL 中的 token 用量白名单字段；跳过聊天正文、prompt、assistant 输出和工具参数。 |
| local_status | False | high | 预留 allowlist 字段读取，不扫描私密目录 |
| official_export | True | exact | 用户显式提供的官方导出 CSV/JSON/JSONL；不读取浏览器、cookie、token 或聊天正文。 |
| snapshot_delta | True | high | 用户显式提供的本地快照文件；只读取会话元信息和 token 数字。 |

## 审计日志

| 时间 | 动作 | 摘要 |
|---|---|---|
| 2026-06-23T12:23:04+00:00 | source_upserted | {"confidence_ceiling": "high", "enabled": true, "source_type": "snapshot_delta"} |
| 2026-06-23T12:23:04+00:00 | snapshot_delta_imported | {"filename": "snapshot-delta.json", "snapshots": 5} |
| 2026-06-23T12:23:04+00:00 | source_upserted | {"confidence_ceiling": "high", "enabled": true, "source_type": "local_codex_rollout"} |
| 2026-06-23T12:23:04+00:00 | local_codex_history_imported | {"files": 1, "imported": 2, "root_hash": "a6d05971f2bf6c82", "skipped_duplicates": 0, "token_records": 2} |
| 2026-06-23T12:23:03+00:00 | source_upserted | {"confidence_ceiling": "exact", "enabled": false, "source_type": "official_export"} |
| 2026-06-23T12:23:03+00:00 | source_upserted | {"confidence_ceiling": "high", "enabled": false, "source_type": "snapshot_delta"} |
| 2026-06-23T12:23:03+00:00 | source_upserted | {"confidence_ceiling": "high", "enabled": false, "source_type": "local_status"} |
| 2026-06-23T12:23:03+00:00 | source_upserted | {"confidence_ceiling": "high", "enabled": false, "source_type": "local_codex_rollout"} |
| 2026-06-23T12:23:03+00:00 | source_upserted | {"confidence_ceiling": "medium", "enabled": false, "source_type": "desktop_visible"} |
| 2026-06-23T12:23:03+00:00 | ledger_initialized | {"db_name": "ledger.db", "source_count": 5} |
| 2026-06-23T12:23:03+00:00 | source_upserted | {"confidence_ceiling": "exact", "enabled": true, "source_type": "official_export"} |
| 2026-06-23T12:23:03+00:00 | official_export_imported | {"filename": "official-export.csv", "format": "csv", "sessions": 3, "snapshots": 3} |
| 2026-06-23T12:23:03+00:00 | source_upserted | {"confidence_ceiling": "exact", "enabled": true, "source_type": "official_export"} |
| 2026-06-23T12:23:03+00:00 | official_export_imported | {"filename": "official-export.jsonl", "format": "jsonl", "sessions": 2, "snapshots": 2} |
| 2026-06-23T12:23:03+00:00 | source_upserted | {"confidence_ceiling": "exact", "enabled": true, "source_type": "official_export"} |
| 2026-06-23T12:23:03+00:00 | official_export_imported | {"filename": "official-export-alt.json", "format": "json", "sessions": 1, "snapshots": 1} |

## 明确不读取

- 浏览器 cookie
- OpenAI token
- 钥匙串和系统凭据
- 聊天正文
- 完整私密路径
