# 脱敏 rollout 样本采集

v0.9.0 继续扩充脱敏 rollout 样本库。真实 Codex rollout 结构可能随版本变化，为了校准字段兼容性，可以让愿意协助校准的用户本地生成脱敏校准样本，再人工确认后提交 issue 或 PR。

仓库内已有三类 synthetic 样本：

- `examples/ledger-samples/local-codex/`：稳定基础样本，用于仓库示例数据流程、watcher 和导入链路。
- `examples/ledger-samples/local-codex-variants/`：字段变体样本，覆盖 `lastTokenUsage`、`totalTokenUsage`、嵌套 `usage`、缺失模型、多项目、多会话等情况。
- `examples/ledger-samples/local-codex-stress/`：压力样本，覆盖多会话重叠、重复快照、异常时间戳、缺失模型、缺项目路径和缺上下文窗口。

## 采集命令

```bash
codex-probe --db .probe/probe.db samples collect-rollout \
  --out reports/ledger/redacted-rollout-samples.jsonl \
  --limit-files 40 \
  --max-records 80
```

## 输出包含

- 时间戳。
- 会话 ID 派生 hash。
- 项目路径 hash。
- turn id hash。
- 模型名。
- input / cached / output / total token 数字。
- credits 是否存在。
- context window 数字。
- source file hash。

## 明确不包含

- 聊天正文。
- prompt。
- assistant 输出。
- 工具参数。
- 完整本地路径。
- cookie。
- token。
- 钥匙串或系统凭据。

## 提交前建议

先人工打开输出文件，确认没有真实正文、真实路径、邮箱、手机号、密钥或公司敏感信息，再提交给维护者。

建议重点说明：

- Codex 版本或大致发布时间。
- 本地系统平台和时区。
- 样本是否来自真实工作流的脱敏输出。
- 是否观察到字段缺失、字段重命名或模型字段为空。

不要提交：

- 原始 `~/.codex` 文件。
- 聊天正文、prompt、assistant 输出或工具参数。
- 完整本地路径。
- cookie、token、Bearer、API key、邮箱或手机号。
