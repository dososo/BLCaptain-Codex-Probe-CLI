# 变更日志

## 未发布

- 暂无。

## 0.9.0 - 2026-06-25

- 新增原生 macOS 状态栏 App：BLCaptain Codex Probe Bar，基于 Swift/AppKit 实现，点击状态栏即可查看本地 Codex 用量摘要。
- 状态栏面板展示 token delta、会话数、预警数、最高消耗会话、建议动作、预算预警、数据源可信度和隐私边界。
- 状态栏面板支持刷新、采集一次、生成/打开 Dashboard、打开报告目录、生成/打开隐私报告和退出。
- App 复用 `codex-probe --json` 命令，不重复实现账本归因逻辑；默认不登录、不读 cookie、不碰 token/钥匙串、不抓包、不上传。
- 新增 `desktop/macos/CodexProbeBar` Swift Package。
- 新增 `scripts/macos/build-codex-probe-bar.sh`，可构建 `build/CodexProbeBar.app`，并写入 `LSUIElement` 菜单栏应用配置。
- 新增 `docs/MACOS_MENUBAR_APP.md` 和 `docs/MACOS_MENUBAR_GOAL.md`，说明状态栏 App 的目标、构建、配置、隐私边界和发布限制。
- 新增 macOS 状态栏 App 契约测试，确保 App 复用 CLI 且不包含 Keychain、cookie、网络请求或抓包能力。
- 新增 macOS 正式分发工程：签名、公证、打包和 preflight 脚本，并明确本地未签名构建与正式 release 的边界。
- 新增 `docs/MACOS_RELEASE_DISTRIBUTION.md`，说明 Developer ID 签名、notarization、公证 stapling、Gatekeeper 验证、普通用户安装体验和发布 `/goal`。

## 0.8.0 - 2026-06-25

- 新增 `codex-probe timeline` 阶段级高消耗时间线，按会话快照计算 token delta 区间，输出阶段标签、风险等级、置信度和建议动作。
- 新增 `codex-probe alerts` 本地预算与停止线预警，覆盖单会话、项目周期、当前范围总账和上下文剩余风险。
- 新增 `codex-probe task-report` 任务类型归因报告，按发布交付、开发实现、验证测试、文档报告、素材生成、调研分析和未知任务聚合消耗。
- 新增 `codex-probe confidence-report` 数据源可信度报告，展示来源、字段覆盖、缺失字段、置信上限、诊断和隐私边界。
- Dashboard 首屏新增今日 token、本周 token、高风险会话、该停会话、本地预算预警、数据源可信度和任务类型归因。
- `watch status-page` 新增最近预警摘要，帮助用户从 watcher 入口判断是否该停止长会话。
- `setup --demo` 自动生成 `timeline.md`、`alerts.md`、`source-confidence.md` 和 `task-report.md`，普通用户一条命令即可看到新增治理报告。
- 扩充 synthetic rollout 样本库，新增 `examples/ledger-samples/local-codex-stress/`，覆盖多会话重叠、重复快照、异常时间戳、缺失模型、缺项目路径和缺上下文窗口。
- 更新报告契约测试和端到端验收脚本，覆盖 timeline、alerts、task report、confidence report 和 Dashboard 新模块。
- 刷新中英文 README、示例报告和 Dashboard 截图，继续强调本地优先、不读取登录态、不替代官方账单。

## 0.7.0 - 2026-06-25

- 新增 `codex-probe projects` 项目级聚合报告，按项目汇总 token delta、credits delta、会话数、最高消耗会话、置信度分布和建议动作。
- 新增 `codex-probe weekly-report` Codex 周报，按本地系统时区的 ISO 周汇总会话、项目、最高消耗会话和治理建议。
- 扩充 synthetic rollout 样本库，新增 `examples/ledger-samples/local-codex-variants/`，覆盖字段别名、缺失模型、多项目、多会话和不同 Codex schema 变体。
- 增强本地 rollout 解析，支持 `lastTokenUsage`、`totalTokenUsage`、嵌套 `usage`、`modelInfo`、`project.path` 等字段结构；缺失模型时显示未知，不再猜测。
- 新增 HTML / JSON 报告契约测试，覆盖 sessions、project summary、weekly report、privacy report 和 dashboard 核心结构。
- 增强 Skill / 输出体检规则，拆分自动安装、绕登录/计费、请求拦截、外传数据、伪装真人和过度承诺等风险类型。
- 新增 `docs/INSTALL.md`，说明 Codex 桌面版、仓库脚本、uvx、pipx 和 Homebrew Formula 草案。
- 新增 `docs/MENUBAR_OR_DESKTOP_EVAL.md`，评估菜单栏 App / 桌面组件路线，并明确不读取登录态、cookie、token 或钥匙串。
- 优化 `setup` 和 `sessions` 的普通用户输出；`--json` 保持机器可读，非 JSON 模式更适合人读。
- 修正 README 会话级 Token 账本示例：统一公开样本模型字段为 `gpt-5.5`，并说明模型列来自数据源 `model` 字段，CLI 不猜测或强制改写。
- 完善 README 和 Codex 桌面版提示词，增加安全 demo、本地历史分析、单次 `/status` 三类普通用户入口。
- 将“开发者安装”改为“安装与体验”，补充可直接让 Codex 桌面版安装 GitHub 仓库的提示词。

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
