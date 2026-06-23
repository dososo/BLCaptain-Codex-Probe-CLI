# 变更日志

## 0.6.0 - 2026-06-23

- 新增 `codex-probe setup`，支持一条命令完成初始化、local history dry-run、报告生成和 Dashboard 打开；`--demo` 可安全使用仓库 synthetic 样本。
- 新增 `scripts/setup-local.sh`，可创建 `.venv`、安装 CLI 并运行安全 demo。
- Dashboard 新增项目、开始日期、结束日期、置信度和模型筛选。
- 新增 `codex-probe watch status-page`，生成本地 watcher 状态页，展示运行状态、最近日志和会话排行。
- 新增 `codex-probe samples collect-rollout`，生成只含白名单字段和哈希的脱敏 rollout 校准样本。
- 新增 `docs/SAMPLE_COLLECTION.md`，说明 beta 用户如何生成和检查脱敏样本。

## 0.5.0 - 2026-06-23

- 新增真实本地数据源接入：`ledger import-history --source local-codex` 可从 Codex rollout JSONL 的 token 用量白名单字段导入历史快照。
- 新增 `ledger import-history --dry-run`，可先预览文件数、token 记录数、可导入记录数和跳过正文行数，不写入业务数据。
- 新增官方导出适配：`ledger inspect-export`、`ledger map-export`、CSV / JSON / JSONL 支持、字段别名和 mapping JSON。
- 新增 `sources doctor --deep`，安全检查本机 Codex 结构化日志覆盖率，只输出哈希、计数和字段覆盖率，不输出完整路径或正文。
- 新增真实 watcher：`watch once/start/status/logs/stop`，支持 PID、状态文件、lock、日志、最近采集时间、错误和采集次数。
- 新增 `delete --watcher --yes`，可删除 watcher 状态、日志和控制文件。
- 增强 Dashboard，加入总览、会话排行、单会话详情摘要和隐私边界。
- 新增 macOS LaunchAgent 安装/卸载脚本和 `docs/MACOS_WATCHER.md`。
- 新增 JSON、JSONL、mapping 和 synthetic rollout 脱敏样本，并刷新示例报告和 Dashboard 截图。
- 更新中英文 README、隐私文档、桌面版提示词、发布清单、测试和验收脚本。

## 0.4.0 - 2026-06-23

- 新增本地 Codex 会话级 Token 账本，回答「token/credits 具体消耗在哪个会话、哪个项目、哪个时间段」。
- 新增 `codex-probe sources doctor`，只探测安全可用数据源，不读取聊天正文、cookie、token 或系统凭据。
- 新增 `codex-probe ledger init` 和 `codex-probe ledger import`，支持用户显式提供的官方导出 CSV/JSON 与本地快照 delta。
- 新增 `codex-probe sessions`、`session-report`、`ledger-report`，输出会话排行、单会话时间线和总账报告。
- 新增 `codex-probe dashboard`，生成本地 HTML Dashboard，展示总览、会话排行、token delta、credits 和置信度。
- 新增 `codex-probe privacy inspect` 与 `delete --ledger --yes`，支持隐私审计和一键删除账本业务数据。
- 新增 `examples/ledger-samples/` 脱敏样本库，覆盖 `exact`、`high`、`medium`、`low` 四类置信度。
- 更新中英文 README、隐私文档和 Codex 桌面版一句话入口。

## 0.3.2 - 2026-06-22

- 新增 `examples/status-samples/` 脱敏 `/status` 样本库，覆盖继续、降配、停止和英文格式场景。
- 增强英文 `/status` 解析，支持 `Context remaining`、`19% remaining` 和 `resets at` 等常见表达。
- 新增样本库单元测试，确保样本能解析出上下文、5 小时额度、7 天额度和预期决策。
- 新增 `assets/screenshots/status-sample-library.svg` 工作例图，并同步刷新中英文 README。
- 更新小红书推荐短文，突出样本库、doctor 和决策卡片。
- 移除中文 README 中效果较弱的旧执行截图和对应图片文件。

## 0.3.1 - 2026-06-22

- 增强 Codex 桌面版 `/status` 解析：单独识别上下文剩余、已用/上限 token、5 小时额度、7 天额度和重置时间。
- 任务级用量报告新增「决策卡片」，直接输出建议动作、为什么贵、怎么降配、什么时候该停。
- 新增 `codex-probe doctor` 一键体检命令，可同时生成用量报告、Skill / 输出体检报告和 doctor 汇总报告。
- 新增 `examples/status-codex-desktop.txt` 脱敏桌面版状态样本。
- 刷新中英文 README，补充 doctor 用法和本地隐私边界说明。

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
