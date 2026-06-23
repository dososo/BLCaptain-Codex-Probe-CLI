# v0.4.0 本地 Codex 会话级 Token 账本执行清单

目标：基于 `outputs/codex-session-token-ledger-prd.md`，把 BLCaptain Codex Probe CLI 从 `/status` 用量体检升级为「本地 Codex 会话级 Token 账本」，达到 GitHub 开源可发布标准。

成功标准：

- 能回答「Codex token/credits 具体消耗在哪个会话、哪个项目、哪个时间段」。
- 支持会话排行、会话详情时间线、token delta、高消耗区间、数据源、置信度。
- 严格本地优先：不读浏览器 cookie，不碰 token，不读钥匙串，不抓包，不读取聊天正文，不上传云端。
- README、英文 README、隐私文档、示例数据、测试和验收脚本同步更新。

## 1. 调研

- [x] 读取 PRD，确认 v0.4.0 的核心不再是单次 `/status` 报告，而是会话级 Token 账本。
- [x] 检查当前 git 状态、版本号和已有改动。
- [x] 读取现有 CLI、storage、reports、测试、README 和验收脚本。
- [x] 识别无关未跟踪素材：`assets/xiaohongshu/` 不纳入本次 v0.4.0 提交。

## 2. 分析

- [x] 确认可复用现有 Python CLI、SQLite、Markdown 报告和测试结构。
- [x] 确认 P0 可用轻量本地 HTML Dashboard，不先做完整桌面插件。
- [x] 确认官方导入和快照 delta 是 P0 最小可交付数据源。
- [x] 确认隐私边界：只处理用户显式提供文件和 allowlist 字段。

## 3. 计划

- [x] 建立 v0.4.0 执行清单。
- [x] 开发完成后补写 Review，记录验证结果、审计结果和剩余风险。

## 4. 开发

- [x] 新增 ledger 数据模型与 SQLite schema。
- [x] 新增 Source Doctor。
- [x] 新增 official_export 与 snapshot_delta 导入。
- [x] 新增 ledger CLI 命令：init、import、watch、sessions、session-report、ledger-report、privacy inspect、dashboard、delete --ledger。
- [x] 新增会话排行、单会话、总账和隐私审计报告。
- [x] 新增示例数据和示例报告。
- [x] 更新 README.md、README.en.md、docs/PRIVACY_SECURITY.md、docs/CODEX_DESKTOP_PROMPT.md。
- [x] 更新验收脚本，覆盖 ledger 端到端链路。

## 5. 验证

- [x] 手工跑通 ledger 初始化、数据源检查、导入、sessions、报告生成。
- [x] 修复 snapshot 首条 baseline 被误算为 delta 的问题。
- [x] 修复 ledger 汇总 join 导致 delta 被放大的问题。
- [x] 重新跑完整端到端验收脚本。
- [x] 验证 Dashboard 或本地 HTML 页面非空、可读、无明显遮挡。

## 6. 测试

- [x] 新增 ledger 单元测试和 CLI e2e 测试。
- [x] 运行 `python3 -m unittest discover -s tests` 并通过。
- [x] 运行 `python3 -m compileall src/codex_usage_skill_probe` 并通过。
- [x] 更新验收脚本后重新运行完整测试、编译检查和 acceptance。

## 7. 审计验收

- [x] 扫描敏感信息：API key、cookie、token、Bearer、GitHub token、邮箱、手机号、`/Users/` 私密路径。
- [x] 检查不提交 `.probe/`、`reports/`、`acceptance-artifacts/`、虚拟环境、数据库、`.DS_Store`、临时截图和无关素材。
- [x] 展示 staged 文件清单和敏感扫描结果。
- [x] 本地 commit 前确认只包含本项目 v0.4.0 相关文件。

## 8. 总结

- [x] 输出改动摘要、测试结果、审计结果、报告路径、剩余风险和是否建议进入 beta。

## Review

- 功能结果：v0.4.0 已新增本地 Codex 会话级 Token 账本，支持 `sources doctor`、`ledger init/import`、`watch start/status/stop`、`sessions`、`session-report`、`ledger-report`、`privacy inspect`、`dashboard` 和 `delete --ledger --yes`。
- 文档结果：README、README.en.md、CHANGELOG、隐私文档、Codex 桌面版提示词和发布清单已同步到 v0.4.0。
- 示例结果：新增 `examples/ledger-samples/` 和 `examples/reports/ledger/`，覆盖 exact / high / medium / low 置信度；新增 `assets/screenshots/ledger-dashboard.png`。
- 验证结果：`python3 -m unittest discover -s tests` 通过 13 个测试；`python3 -m compileall src tests scripts/run_acceptance.py` 通过；`scripts/run_acceptance.py` 通过，证据目录为 `acceptance-artifacts/20260623T115715Z/`。
- 安装结果：临时虚拟环境中 `python -m pip install .` 通过，安装后 `codex-probe --version` 返回 `codex-probe 0.4.0`。
- 审计结果：staged 文件为 29 个，未包含 `.probe/`、`reports/`、`acceptance-artifacts/`、虚拟环境、数据库、`.DS_Store` 或 `assets/xiaohongshu/`；敏感扫描仅命中 README 公开联系邮箱和测试断言字面量 `cookie=`。
- 剩余风险：P0 的 `watch start` 仍是显式状态记录，不是后台采集 daemon；Dashboard 是本地静态 HTML，不是完整交互式桌面插件；真实用户官方导出格式仍需 beta 样本继续校准。
- beta 建议：建议进入小范围 beta，重点收集真实脱敏官方导出和快照样本，验证归因置信度与用户理解成本。
