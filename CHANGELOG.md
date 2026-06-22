# 变更日志

## 0.3.0 - 2026-06-22

- 支持 Codex 桌面版中文 `/status` 文本格式解析。
- 新增 Codex 桌面版一句话使用方式和中英文 README。
- 新增真实报告配图、示例报告和优化版 Skill 样例。
- 优化脱敏证据片段，避免截断 `[REDACTED:...]` 标记。
- 收窄 `.gitignore`，避免个人 `.probe/` 和根目录 `reports/` 被误提交，同时允许提交 `examples/reports/` 示例报告。

## 0.1.0 - 2026-06-20

- 初始化 BLCaptain Codex Probe CLI，本地只读 CLI 探针。
- 支持 `/status` 文本和手工 JSON 用量导入。
- 支持任务级 Token/额度用量报告。
- 支持 Skill/输出质量体检报告。
- 支持敏感信息脱敏、本地 SQLite、审计日志和业务数据删除。
- 添加示例数据、自动化测试、端到端验收脚本和 CI。
