# 脱敏 rollout 样本采集

v0.6.0 开始支持脱敏 rollout 样本采集。真实 Codex rollout 结构可能随版本变化，为了校准字段兼容性，可以让 beta 用户本地生成脱敏校准样本，再人工确认后提交 issue 或 PR。

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
