# v0.5.0 真实数据源与稳定 Watcher 执行清单

目标：基于 `outputs/codex-session-token-ledger-prd.md` 和本轮 `/goal`，把 BLCaptain Codex Probe CLI 从 v0.4.0「本地会话级 Token 账本框架」升级为 v0.5.0「真实数据源接入 + 稳定 watcher + 可发布 beta 产品」。

成功标准：

- 能尽最大努力回答「Codex token 具体消耗在哪个会话、哪个项目、哪个时间段」。
- 能自动检测并安全读取本机 Codex 结构化 rollout 日志中的 token 用量字段；如果没有 token 字段，只导入元信息或明确说明无法精确归因。
- 支持官方导出 CSV / JSON / JSONL、字段别名、mapping JSON、导出结构检查和 dry-run。
- 支持 `watch once`、真实后台 `watch start/status/stop/logs`、PID/lock/status/log、崩溃状态识别和 `delete --watcher --yes`。
- Dashboard 覆盖总览、会话排行、单会话详情和隐私边界，工具型、可读、无营销页。
- 严格本地优先：不读浏览器 cookie，不碰 token，不读钥匙串，不抓包，不读取聊天正文、prompt、assistant 输出，不上传云端。
- README、英文 README、隐私文档、macOS 入口文档、示例数据、测试和验收脚本同步更新。

## 1. 调研

- [x] 读取 `/goal` 附件，确认 v0.5.0 目标、命令要求、隐私边界和不自动 push 要求。
- [x] 检查当前 git 状态、版本号和已有 commit。
- [x] 读取 v0.4.0 CLI、ledger adapter、storage、source doctor、report、测试和验收脚本。
- [x] 安全探测 `~/.codex` 文件结构，只读取文件名、schema key、计数和哈希，不读取正文内容。
- [x] 确认本机 Codex rollout JSONL 中存在 `last_token_usage`、`total_token_usage`、`rate_limits`、`turn_id`、`model` 等可白名单读取字段。
- [x] 识别无关未跟踪素材：`assets/xiaohongshu/` 不纳入本次 v0.5.0 提交。

## 2. 分析

- [x] 确认可在现有 Python CLI + SQLite 架构内扩展，不需要重做为桌面 App。
- [x] 确认「自动读取所有历史」的真实边界：只有本地结构化日志含 token 字段时才可导入；不伪造缺失用量。
- [x] 确认 local Codex 历史导入必须只取 allowlist 字段，路径默认哈希，不显示完整私密路径。
- [x] 确认 watcher P0 应是稳定后台进程和状态文件，不读取聊天正文。
- [x] 确认 Dashboard 和文档措辞不承诺省钱、绕限制、替代官方账单。

## 3. 计划

- [x] 建立 v0.5.0 执行清单。
- [x] 更新发布检查清单到 v0.5.0。
- [x] 先补数据源适配和测试，再接 watcher，最后刷新文档和示例。
- [x] 开发完成后补写 Review，记录验证结果、审计结果和剩余风险。

## 4. 开发

- [x] 升级版本号到 v0.5.0。
- [x] 新增官方导出 inspect / map / JSONL / mapping 支持。
- [x] 新增 local Codex rollout 历史导入和 dry-run。
- [x] 新增 `sources doctor --deep`，展示安全数据源覆盖率、token 字段计数和隐私边界。
- [x] 新增真实 watcher：`watch once/start/status/stop/logs`。
- [x] 新增 `delete --watcher --yes`。
- [x] 增强 Dashboard：总览、会话排行、单会话详情、隐私页。
- [x] 新增 macOS LaunchAgent 安装/卸载脚本和文档。
- [x] 新增示例数据：CSV、JSON、JSONL、mapping、synthetic rollout。
- [x] 更新 README.md、README.en.md、CHANGELOG.md、docs/PRIVACY_SECURITY.md、docs/CODEX_DESKTOP_PROMPT.md。
- [x] 更新验收脚本，覆盖 v0.5.0 端到端链路。

## 5. 验证

- [x] 手工跑通导出 inspect / map / import。
- [x] 手工跑通 local history dry-run 和 synthetic rollout 导入。
- [x] 手工跑通 `sources doctor --deep`，确认不输出完整私密路径和正文。
- [x] 手工跑通 `watch once/start/status/logs/stop`，确认 PID、lock、日志和崩溃状态。
- [x] 验证 Dashboard 页面非空、可读、无明显遮挡、不展示敏感数据。

## 6. 测试

- [x] 新增/更新单元测试覆盖 official export mapping、JSONL、local history、watcher、delete watcher。
- [x] 运行 `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests` 并通过。
- [x] 运行 `PYTHONDONTWRITEBYTECODE=1 python3 -m compileall src tests scripts/run_acceptance.py` 并通过。
- [x] 运行 `PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_acceptance.py` 并通过。

## 7. 审计验收

- [x] 扫描敏感信息：API key、cookie、token、Bearer、GitHub token、邮箱、手机号、`/Users/` 私密路径。
- [x] 检查不提交 `.probe/`、`reports/`、`acceptance-artifacts/`、虚拟环境、数据库、`.DS_Store`、临时截图和无关素材。
- [x] 展示 staged 文件清单和敏感扫描结果。
- [x] 本地 commit 前确认只包含本项目 v0.5.0 相关文件。

## 8. 总结

- [x] 输出改动摘要、测试结果、审计结果、报告路径、剩余风险和是否建议进入 beta。

## Review

- 功能结果：v0.5.0 已新增 official export inspect / map / JSONL / mapping、本地 Codex rollout 历史导入、dry-run、`sources doctor --deep`、真实 watcher、`delete --watcher --yes`、增强 Dashboard 和 macOS LaunchAgent 入口。
- 数据源结果：本机安全调研确认 Codex rollout JSONL 存在 token 用量字段；实现只处理 token 用量白名单字段，跳过正文、prompt、assistant 输出和工具参数，完整路径默认哈希。
- 文档结果：README、README.en.md、CHANGELOG、隐私文档、Codex 桌面版提示词、macOS watcher 文档、发布清单和样本说明已同步 v0.5.0。
- 示例结果：新增 CSV / JSON / JSONL / mapping / synthetic rollout 样本；刷新 `examples/reports/ledger/` 和 `assets/screenshots/ledger-dashboard.png`。
- 验证结果：`python3 -m unittest discover -s tests` 通过 17 个测试；`python3 -m compileall src tests scripts/run_acceptance.py` 通过；`scripts/run_acceptance.py` 通过，证据目录为 `acceptance-artifacts/20260623T124426Z/`。
- 安装结果：临时虚拟环境中 `python -m pip install .` 通过，安装后 `codex-probe --version` 返回 `codex-probe 0.5.0`。
- 审计结果：候选文件 28 个，敏感扫描仅命中说明性 `/Users/` 文案、测试断言字面量 `cookie=` 和 README 公开邮箱；未命中手机号、真实 API key、Bearer、GitHub token、cookie 或私密路径。
- 剩余风险：真实 Codex rollout schema 可能随版本变化，仍需 beta 样本校准；local history 只能在 token 字段存在时精细归因；watcher 是 LaunchAgent/后台进程入口，不是完整菜单栏 App。
- beta 建议：建议进入公开 beta，但 README 必须继续强调本地优先、不可替代官方账单、不能保证省钱、不能伪造缺失 token。

## v0.5.0 严谨性补充

- [x] 明确 `credits` 是来源提供的 credits / cost / quota 数值，不等同于美元、人民币或官方账单金额。
- [x] 明确 `credits delta` 只在同一来源同一口径可解释为消耗差值时展示；无法确认时显示 `未知`。
- [x] 会话排行、总账报告、单会话详情和 Dashboard 已增加本机时区开始/结束时间。
- [x] 报告已补充置信度和建议阈值说明，避免把治理建议误读为官方账单判断。
- [x] 新增测试覆盖本机时区展示和严谨性说明。
- [x] 重新生成示例报告和 Dashboard 截图；验收脚本通过，证据目录为 `acceptance-artifacts/20260623T123159Z/`。

## 产品化补充

- [x] 新增 `codex-probe setup`，支持初始化、dry-run、demo 样本导入、报告生成和 Dashboard 打开。
- [x] 新增 `scripts/setup-local.sh`，支持创建 `.venv`、安装 CLI 并运行安全 demo。
- [x] Dashboard 新增项目、开始日期、结束日期、置信度和模型筛选。
- [x] 新增 `codex-probe watch status-page`，生成本地 watcher 状态页。
- [x] 新增 `codex-probe samples collect-rollout` 和 `docs/SAMPLE_COLLECTION.md`，用于真实脱敏 rollout 样本校准。
- [x] 新增测试和 acceptance 覆盖；验收脚本通过，证据目录为 `acceptance-artifacts/20260623T124957Z/`。

## v0.6.0 发布补充

- [x] 将包版本、CLI 版本、README badge、发布验收标准和 CHANGELOG 同步到 `0.6.0`。
- [x] 中英文 README 已补充一键 setup、Dashboard 筛选、watcher 状态页和脱敏 rollout 样本采集。
- [x] 安装 smoke 通过：临时虚拟环境中 `python -m pip install .` 成功，`codex-probe --version` 返回 `codex-probe 0.6.0`。

## README 模型示例修正

- [x] 确认模型列来自示例数据和数据源 `model` 字段，不是解析器误判。
- [x] 将 ledger 公开样本统一为 `gpt-5.5`，避免 README 截图出现旧模型名。
- [x] 补充 README 说明：CLI 原样展示数据源模型字段，不会猜测或强制改写。
- [x] 重新生成示例报告、Dashboard HTML 和 README PNG 截图。
- [x] 验证通过：17 个单元测试、compileall、acceptance；证据目录为 `acceptance-artifacts/20260623T130952Z/`。
- [x] 审计通过：候选文件 18 个，敏感扫描仅命中说明性文本、测试断言和 README 公开邮箱；旧模型名仅保留在测试禁止断言中。

## 普通用户入口补充

- [x] 将 README 顶部 Codex 桌面版入口从单句扩展为安全 demo、本地历史分析、单次 `/status` 三类可复制提示词。
- [x] 同步 README 正文和 `docs/CODEX_DESKTOP_PROMPT.md`。
- [x] 明确每类入口的报告路径、隐私边界和最终解释要求。
- [x] 将“开发者安装”改为“安装与体验”，补充可让 Codex 桌面版直接安装 GitHub 仓库的提示词。

# v0.7.0 Roadmap 执行清单

目标：基于当前 Roadmap，把 BLCaptain Codex Probe CLI 从 v0.6.0 的「会话级账本 + watcher + Dashboard」推进为 v0.7.0 的「样本校准、项目级治理、周报、报告契约测试、细粒度 Skill 风险和轻安装准备」。

成功标准：

- Roadmap 六个模块均有交付：已实现、已文档化，或因风险被明确评估并给出下一步。
- 普通用户能通过 Codex 桌面版提示词、安全 demo、uvx/pipx 文档理解怎么开始。
- CLI 能输出项目级聚合和周报，并区分 `credits` 来源值、估算值和置信度。
- 样本库覆盖更多字段结构和缺失字段场景，且不含真实正文、token、cookie、邮箱、手机号或完整私密路径。
- HTML / JSON 报告契约测试能保护 Dashboard、sessions、ledger、project summary、weekly report、privacy report 核心结构。
- Skill 体检风险类型更细，证据脱敏，建议可执行。
- 菜单栏 App / 桌面组件有明确评估文档，不牺牲 local-first 边界。

## 1. 调研

- [x] 读取 goal objective，确认 8 步流程、6 个模块、隐私边界和暂停条件。
- [x] 检查 git 状态，确认未跟踪 `assets/xiaohongshu/` 不纳入本轮改动。
- [x] 阅读 README、README.en、CHANGELOG、tasks/lessons、tasks/todo。
- [x] 阅读 CLI、ledger storage/report/adapters/local history、Skill linter、测试和样本库。
- [x] 确认现有 `projects` 表和 `ledger_summary` 可支撑项目聚合，无需重构数据库 schema。

## 2. 分析

- [x] 真实脱敏 rollout 样本库：本轮补 synthetic/redacted 结构变体和说明，不提交真实本机数据。
- [x] 项目级聚合和周报：在现有会话摘要上聚合，新增 CLI 命令和 Markdown/JSON 输出。
- [x] HTML / JSON schema 快照测试：新增结构契约测试，避免硬编码时间戳。
- [x] Skill 风险规则：拆分插件、登录/计费绕过、外传、伪装真人、过度承诺等 finding_type。
- [x] Homebrew / uvx：优先补可执行轻安装说明和 Homebrew Formula 草案，不假装 tap 已发布。
- [x] 菜单栏 App / 桌面组件：本轮做评估文档和推荐路径，不强行做需要签名/权限的新 App。

## 3. 计划

- [x] 在 `tasks/todo.md` 写入 v0.7.0 执行清单。
- [x] 开发完成后逐项更新本清单状态。
- [x] Review 段记录验证结果、审计结果、剩余风险和发布建议。

## 4. 开发

- [x] 新增项目级聚合数据结构、Markdown 渲染、JSON payload 和 `codex-probe projects` 命令。
- [x] 新增周报 Markdown/JSON 渲染和 `codex-probe weekly-report` 命令。
- [x] 让 `setup --demo` 同步生成项目汇总和周报示例报告。
- [x] 收敛 `sessions` 普通模式输出：普通模式只输出人读 Markdown，`--json` 输出结构化 JSON。
- [x] 扩充 `examples/ledger-samples/local-codex-variants/` synthetic rollout 样本，覆盖字段别名、缺失模型、多项目和多会话。
- [x] 更新 `examples/ledger-samples/README.md` 和 `docs/SAMPLE_COLLECTION.md`。
- [x] 增强 `skill_linter.py` 细粒度风险规则和测试。
- [x] 新增 JSON / HTML 报告契约测试。
- [x] 新增 `docs/INSTALL.md` 和 Homebrew Formula 草案文档。
- [x] 新增 `docs/MENUBAR_OR_DESKTOP_EVAL.md`。
- [x] 更新 README、README.en、CHANGELOG、发布验收说明和示例报告。
- [x] 更新版本号到 `0.7.0`。

## 5. 验证

- [x] 使用 demo 样本跑通 `setup --demo`，检查 Dashboard、sessions、ledger、project summary、weekly report、privacy report。
- [x] 手工跑通 `projects --range 30d` 和 `weekly-report --range 30d` 的 Markdown / JSON 输出。
- [x] 检查时间显示使用系统时区，`credits` 仍说明为来源值。
- [x] 检查 README 普通用户路径与新增命令一致。
- [x] 检查示例报告无真实隐私信息、无误导字段。

## 6. 测试

- [x] 运行 `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests`。
- [x] 运行 `PYTHONDONTWRITEBYTECODE=1 python3 -m compileall src tests scripts/run_acceptance.py`。
- [x] 运行 `PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_acceptance.py`。
- [x] 运行 clean install smoke 或 `scripts/setup-local.sh` 等价流程。

## 7. 审计验收

- [x] 检查 git diff 只包含本项目 Roadmap 相关文件。
- [x] 敏感扫描候选文件，排除真实 key、token、cookie、Bearer、GitHub token、邮箱、手机号、完整私密路径、真实聊天正文。
- [x] 确认 `.probe/`、`reports/` 根目录、虚拟环境、acceptance-artifacts、本机临时目录、真实 `~/.codex` 原始数据和 `assets/xiaohongshu/` 未进入提交候选。
- [x] 确认 README/文档不承诺省钱、绕额度、读取官方隐藏数据或替代官方账单。

## 8. 总结

- [x] 输出本轮改动摘要、测试结果、审计结果、是否建议发布和 remaining risks。

## Review

- 功能结果：v0.7.0 已新增 `projects` 项目级聚合、`weekly-report` 周报、setup 项目/周报产物、普通模式更友好的 `setup` 和 `sessions` 输出。
- 样本结果：新增 `examples/ledger-samples/local-codex-variants/`，覆盖 `lastTokenUsage`、`totalTokenUsage`、嵌套 `usage`、缺失模型、多项目和多会话；解析器缺失模型时保持未知，不再猜测。
- 质量结果：新增 `tests/test_report_contracts.py`，覆盖 sessions、projects、weekly、privacy 和 dashboard 的 JSON/HTML 结构；Skill 体检拆分自动安装、绕登录/计费、请求拦截、外传数据、伪装真人和过度承诺。
- 文档结果：README、README.en、CHANGELOG、隐私文档、Codex 桌面版提示词、样本采集文档、发布清单、安装文档和桌面入口评估已同步。
- 验证结果：21 个单元/端到端测试通过；compileall 通过；acceptance 通过，证据目录为 `acceptance-artifacts/20260625T111151Z/`；clean install smoke 通过，安装后 `codex-probe --version` 返回 `codex-probe 0.7.0`。
- 审计结果：候选改动集中在本项目 Roadmap 文件；`.probe/`、根目录 `reports/`、虚拟环境、acceptance-artifacts、真实 `~/.codex` 数据和无关 `assets/xiaohongshu/` 未纳入。
- 剩余风险：真实 Codex rollout schema 仍可能随版本变化，需要持续收集真实脱敏样本；Homebrew tap 与 PyPI 发布尚未实际执行；菜单栏 App 仍停留在评估阶段。

# v0.8.0 Codex 单工具用量透明度深化清单

目标：基于当前 v0.7.0，把 BLCaptain Codex Probe CLI 从「会话级账本 + 项目/周报」推进到「阶段级时间线、预算预警、任务归因、数据源可信度产品化和更低门槛入口」。

成功标准：

- 用户能看到一个会话内 token delta 具体在哪些时间区间增长，并得到阶段标签、风险等级和建议动作。
- 用户能设置或使用默认本地预算阈值，输出单会话、项目周、总账周期和上下文剩余风险预警。
- 项目、任务和数据来源的归因更清楚；无法确认的字段必须显示未知或低置信，不伪造。
- Markdown、JSON、Dashboard、watcher 状态页都说明数字来源、字段口径、缺失字段和为什么不能更精确。
- 样本库新增更多 synthetic / redacted rollout 变体，覆盖字段别名、缺字段、重复快照、多会话重叠、异常时间戳、模型缺失、上下文窗口缺失和项目路径缺失。
- 普通用户入口继续降低门槛，`setup --demo` 能生成阶段时间线、预算预警、可信度和任务归因报告。
- 严格本地优先：不登录 OpenAI，不读浏览器 cookie、token、钥匙串或系统凭据，不抓包，不读取聊天正文，不上传数据。

## 1. 调研

- [x] 读取 v0.8.0 `/goal` 附件，确认 8 步流程、6 个模块和隐私边界。
- [x] 检查当前 dirty 工作树，确认 v0.7.0 改动是本轮基线，避开无关 `assets/xiaohongshu/`。
- [x] 阅读 ledger models、storage、reports、CLI、local history、测试、验收脚本和样本库。
- [x] 确认现有 `usage_snapshots` / `usage_deltas` 足够支撑阶段级时间线，无需新增数据库表。

## 2. 分析

- [x] 阶段级时间线：基于相邻 snapshot 或已有 delta 计算区间增长，阶段标签采用保守启发式。
- [x] 额度预警：使用默认阈值和 CLI 参数，不替代官方账单，不承诺省钱。
- [x] 项目/任务归因：在现有项目聚合上增加任务类型推断和项目别名说明；低证据保持未知。
- [x] 数据源可信度：把来源、字段覆盖、缺失字段、口径和隐私边界做成报告与 Dashboard 模块。
- [x] 样本库：只补 synthetic / redacted 样本，不提交真实本机历史或聊天内容。
- [x] 普通用户入口：让 setup 自动生成新增报告，并保持 `--json` 给机器、普通输出给人。

## 3. 计划

- [x] 在 `tasks/todo.md` 追加 v0.8.0 执行清单。
- [x] 新增数据结构、聚合函数和 Markdown/HTML 渲染。
- [x] 新增 CLI 命令和 setup 产物。
- [x] 扩充样本库与示例报告。
- [x] 更新 README、README.en、CHANGELOG、隐私与发布文档。
- [x] 运行测试、验收、安装 smoke 和隐私审计。

## 4. 开发

- [x] 新增阶段级时间线模型、聚合、报告和 `codex-probe timeline`。
- [x] 新增预算预警模型、报告和 `codex-probe alerts`。
- [x] 新增任务类型归因模型、报告和 `codex-probe task-report`。
- [x] 新增数据源可信度报告和 `codex-probe confidence-report`。
- [x] Dashboard 增加今日、本周、高风险会话、该停会话和数据源可信度摘要。
- [x] watcher 状态页增加最近预警摘要。
- [x] `setup --demo` 生成 timeline、alerts、confidence、task-report。
- [x] 扩充 `examples/ledger-samples/` synthetic rollout 变体。
- [x] 更新版本号到 `0.8.0`。

## 5. 验证

- [x] 重新生成 `examples/reports/ledger/` 示例报告。
- [x] 重新生成 `assets/screenshots/ledger-dashboard.png`。
- [x] 手工检查 Markdown 和 Dashboard 不展示敏感信息。
- [x] 检查普通输出可读，JSON 输出结构稳定。

## 6. 测试

- [x] `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests`
- [x] `PYTHONDONTWRITEBYTECODE=1 python3 -m compileall src tests scripts/run_acceptance.py`
- [x] `PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_acceptance.py`
- [x] clean install smoke：干净 venv 安装、`codex-probe --version`、`codex-probe setup --demo --no-open`

## 7. 审计验收

- [x] 检查 git diff 只包含 v0.8.0 相关项目文件。
- [x] 敏感扫描：key、token、cookie、Bearer、GitHub token、邮箱、手机号、完整私密路径、真实聊天正文。
- [x] 确认 `.probe/`、根目录 `reports/`、`.venv/`、acceptance-artifacts、真实 `~/.codex` 原始数据和无关素材未进入候选。
- [x] 检查 README/报告不承诺省钱、官方精确账单、绕额度、绕登录或读取隐藏官方数据。

## 8. 总结

- [x] 写入 Review：改动摘要、验证结果、测试结果、审计结果、发布判断和剩余风险。

## Review

- 功能结果：v0.8.0 已新增 `timeline`、`alerts`、`task-report`、`confidence-report` 四个命令；`setup --demo` 会自动生成新增报告；Dashboard 增加今日、本周、高风险会话、该停会话、预算预警、数据源可信度和任务归因；watcher 状态页增加最近预警。
- 样本结果：新增 `examples/ledger-samples/local-codex-stress/`，覆盖多会话重叠、重复快照、异常时间戳、缺失模型、缺项目路径和缺上下文窗口。
- 文档结果：README、README.en、CHANGELOG、隐私文档、Codex 桌面版提示词、样本采集文档、安装和发布清单已同步 v0.8.0；示例报告和 Dashboard 截图已刷新。
- 验证结果：22 个单元/端到端测试通过；compileall 通过；acceptance 通过，证据目录为 `acceptance-artifacts/20260625T113800Z/`；clean install smoke 通过，安装后 `codex-probe --version` 返回 `codex-probe 0.8.0`。
- 审计结果：`.probe/`、根目录 `reports/`、`.venv/`、acceptance-artifacts、真实 `~/.codex` 数据和无关 `assets/xiaohongshu/` 未纳入候选；敏感扫描仅命中仓库内假 key / 假手机号 / `cookie=` 测试断言。
- 发布判断：功能已达到 v0.8.0 公开 beta 标准。剩余风险是字段归因仍依赖用户可见数据源；本地 rollout 不是官方账单，缺字段时只能低置信或未知。

# v0.9.0 macOS 状态栏 App 执行清单

目标：基于当前 BLCaptain Codex Probe CLI，交付一个可对外发布的原生 macOS 状态栏 App 第一版，让普通用户不用记命令也能看到 Codex 用量风险、打开 Dashboard、运行一次本地采集。

成功标准：

- 原生 macOS 状态栏 App 可构建、可启动、可点击弹出面板。
- 面板展示总 token、会话数、预警数、最高消耗会话、建议动作、预算预警、数据源可信度和隐私边界。
- 面板提供刷新、采集一次、生成/打开 Dashboard、打开报告目录和退出。
- 核心数据来自 `codex-probe --json`，不重复实现账本归因。
- 不登录、不读 cookie、不碰 token、不读钥匙串、不抓包、不上传。
- README、英文 README、macOS 文档和发布检查清单同步说明。

## 1. 调研

- [x] 读取用户需求，确认目标是对外发布标准的 macOS 状态栏 App。
- [x] 读取 apple-hig skill，确认本地 skill 仅提供 HIG 目录入口。
- [x] 读取 qiaomu-goal-meta-skill，按其结构生成 `/goal` 文档。
- [x] 检查当前仓库结构、Swift 工具链、脚本目录、README 和现有 dirty 工作树。

## 2. 分析

- [x] 确定第一版使用 Swift/AppKit 原生状态栏 App，不引入 Electron。
- [x] 确定数据层通过 CLI JSON 输出获取，避免重复实现 SQLite/账本逻辑。
- [x] 确定默认配置支持 CLI 路径、DB 路径、报告目录和时间范围。
- [x] 确定第一版不做签名、公证、自动登录项和官方账单读取。

## 3. 计划

- [x] 写入 `docs/MACOS_MENUBAR_GOAL.md`。
- [x] 写入本执行清单。
- [x] 实现 App、脚本、测试、文档后逐项更新。

## 4. 开发

- [x] 新增 `desktop/macos/CodexProbeBar` Swift Package。
- [x] 实现状态栏图标、popover 面板、数据模型、CLI Runner 和动作按钮。
- [x] 新增 `.app` 打包脚本。
- [x] 新增 macOS 状态栏 App 文档。
- [x] 更新 README、README.en、CHANGELOG、发布清单。
- [x] 更新版本号到 `0.9.0`。

## 5. 验证

- [x] 用 Swift build 验证 App 可编译。
- [x] 用构建脚本生成 `.app`。
- [x] 用 demo 数据或本地 reports 验证刷新、生成 Dashboard 和打开报告目录。
- [x] 检查 UI 截图或运行输出，确认不简陋、不遮挡关键文案。

## 6. 测试

- [x] `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests`
- [x] `PYTHONDONTWRITEBYTECODE=1 python3 -m compileall src tests scripts/run_acceptance.py`
- [x] `swift build --package-path desktop/macos/CodexProbeBar`
- [x] `scripts/macos/build-codex-probe-bar.sh`

## 7. 审计验收

- [x] 检查 Swift 源码不包含 Keychain、cookie、网络抓包、代理、浏览器读取或上传逻辑。
- [x] 敏感扫描 key、token、cookie、Bearer、GitHub token、邮箱、手机号、完整私密路径。
- [x] 确认 `.probe/`、根目录 `reports/`、`.venv/`、acceptance-artifacts、build/dist、真实 `~/.codex` 和无关素材未纳入候选。
- [x] 检查文档不承诺省钱、官方精确账单、绕额度、绕登录或读取隐藏官方数据。

## 8. 总结

- [x] 写入 Review：实现摘要、验证结果、测试结果、审计结果、发布判断和剩余风险。

## Review

- 功能结果：v0.9.0 已新增原生 macOS 状态栏 App `BLCaptain Codex Probe Bar`，包含状态栏图标、popover 面板、CLI Runner、刷新、采集一次、生成/打开 Dashboard、打开报告目录、生成/打开隐私报告和退出。
- 实现结果：新增 `desktop/macos/CodexProbeBar` Swift Package 和 `scripts/macos/build-codex-probe-bar.sh`，可构建 `build/CodexProbeBar.app`，并写入 `LSUIElement` 菜单栏 App 配置和 `defaults.json`。
- 文档结果：新增 `docs/MACOS_MENUBAR_APP.md` 和 `docs/MACOS_MENUBAR_GOAL.md`；README、README.en、CHANGELOG、安装文档、隐私文档、发布清单、Codex 桌面版提示词和菜单栏评估文档已同步 v0.9.0。
- 验证结果：25 个 Python 测试通过；compileall 通过；`swift build --package-path desktop/macos/CodexProbeBar` 通过；`.app` 打包脚本通过；App 启动后可看到 `CodexProbeBar` 进程，并已正常退出；CLI acceptance 通过，证据目录为 `acceptance-artifacts/20260625T115017Z`；clean install smoke 通过，`codex-probe --version` 返回 `codex-probe 0.9.0`。
- 审计结果：状态栏 App 只调用本地 `codex-probe --json`，未引入 Keychain、HTTPCookie、URLSession、WKWebView、抓包、代理或上传能力；构建产物仍在忽略目录内，不纳入提交候选。
- 发布判断：可作为公开 beta 的 macOS 状态栏入口发布。剩余风险是未做 Developer ID 签名、公证、自动更新和自动登录项；这些属于分发工程，不应以读取登录态或系统凭据为代价。

# v0.9.0 macOS 正式分发加固清单

目标：在现有 BLCaptain Codex Probe Bar 基础上补齐 macOS 正式分发工程，让维护者可以产出签名、公证、可验证的 release 包，并明确当前本地构建与普通用户正式安装之间的差距。

成功标准：

- 本地 `.app` 构建、preflight、打包流程可运行。
- 签名、公证脚本存在，且只通过环境变量读取维护者凭据，不把任何证书、私钥或 Apple 凭据写入仓库。
- 文档明确本地未签名构建不能承诺普通用户无 Gatekeeper 问题。
- 测试覆盖签名、公证、打包、preflight 脚本和凭据不落仓库。
- 审计确认不新增读取 cookie、token、钥匙串、系统凭据、聊天正文、抓包、代理或上传能力。

## 1. 调研

- [x] 读取用户关于 macOS 标准规范、签名、公证、普通用户安装问题的要求。
- [x] 读取 qiaomu-goal-meta-skill，确认 `/goal` 需要写清楚目标、验证、约束、边界和暂停条件。
- [x] 读取 apple-hig skill，确认本地只提供 HIG 目录入口，无额外可执行规范文件。
- [x] 查阅 Apple 官方签名、公证和 hardened runtime 文档入口。
- [x] 检查现有 `build-codex-probe-bar.sh`、macOS 文档、发布清单和测试。

## 2. 分析

- [x] 确认当前状态栏 App 是可构建本地 beta，不是已签名/已公证正式分发包。
- [x] 确认正式发布至少需要 Developer ID 签名、hardened runtime、notarization、stapling、Gatekeeper 验证和 release 包。
- [x] 确认不能在仓库内保存 Apple ID、app-specific password、证书、私钥或 notary 凭据。
- [x] 确认本轮不引入自动更新、安装器、登录项或额外系统权限，避免扩大隐私和发布风险。

## 3. 计划

- [x] 新增签名、公证、打包、preflight 脚本。
- [x] 新增 macOS 正式分发文档和可执行 `/goal`。
- [x] 更新 README、安装文档、状态栏文档、发布清单和变更日志。
- [x] 新增测试并运行完整验证、审计。

## 4. 开发

- [x] 新增 `scripts/macos/sign-codex-probe-bar.sh`。
- [x] 新增 `scripts/macos/notarize-codex-probe-bar.sh`。
- [x] 新增 `scripts/macos/package-codex-probe-bar.sh`。
- [x] 新增 `scripts/macos/preflight-codex-probe-bar.sh`。
- [x] 新增 `docs/MACOS_RELEASE_DISTRIBUTION.md`。
- [x] 更新 README、安装文档、状态栏文档、发布清单和 CHANGELOG。
- [x] 新增 macOS 正式分发契约测试。

## 5. 验证

- [x] 运行 Swift build。
- [x] 运行 `.app` 构建脚本。
- [x] 运行 preflight，确认未签名/未公证被报告为 warning。
- [x] 运行 package `--skip-dmg`，确认可生成 zip。
- [x] 运行正式发布模式 preflight，确认未签名/未公证会失败，不能误判为正式可发布。

## 6. 测试

- [x] `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests`
- [x] `PYTHONDONTWRITEBYTECODE=1 python3 -m compileall src tests scripts/run_acceptance.py`
- [x] `swift build --package-path desktop/macos/CodexProbeBar`
- [x] `scripts/macos/build-codex-probe-bar.sh`
- [x] `scripts/macos/preflight-codex-probe-bar.sh`
- [x] `scripts/macos/package-codex-probe-bar.sh --skip-dmg`
- [x] `PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_acceptance.py`
- [x] `bash -n` 检查四个 macOS 发布脚本。

## 7. 审计验收

- [x] 扫描 key、token、cookie、Bearer、GitHub token、邮箱、手机号、Apple 凭据、证书和私钥。
- [x] 确认不提交 `.probe/`、根目录 `reports/`、`.venv/`、acceptance-artifacts、build、dist、真实 `~/.codex` 原始数据和无关素材。
- [x] 确认文档不承诺未签名版本可无摩擦安装，不建议用户关闭 Gatekeeper。
- [x] 确认 App 和脚本不新增隐私越界能力。

## 8. 总结

- [x] 写入 Review：实现摘要、验证结果、测试结果、审计结果、发布判断和剩余风险。

## Review

- 实现结果：新增 `sign-codex-probe-bar.sh`、`notarize-codex-probe-bar.sh`、`package-codex-probe-bar.sh`、`preflight-codex-probe-bar.sh`，把本地构建、签名、公证、stapling、Gatekeeper 检查和 release zip 打包拆成清晰步骤。
- 文档结果：新增 `docs/MACOS_RELEASE_DISTRIBUTION.md`，并更新 README、安装文档、状态栏文档、发布清单和 CHANGELOG，明确未签名本地构建不能承诺普通用户无摩擦安装。
- 测试结果：29 个 Python 测试通过；compileall 通过；Swift build 通过；`.app` 构建脚本通过；preflight 通过并正确输出未签名/未公证 warning；package `--skip-dmg` 生成 `dist/CodexProbeBar-v0.9.0.zip`；四个 macOS 发布脚本 `bash -n` 语法检查通过；CLI acceptance 通过，证据目录为 `acceptance-artifacts/20260625T132539Z`。
- 审计结果：正式发布模式 `preflight --require-signed --require-notarized` 按预期失败，说明当前产物不会被误判为正式可发布；新增脚本不保存 Apple 凭据、证书或私钥，不读取 cookie、token、钥匙串、聊天正文，也不新增网络上传能力。
- 发布判断：当前仓库达到「开发者本地构建 + 公开 beta 体验 + 维护者正式分发工程已准备」标准；还没有达到「普通用户下载即无摩擦安装」标准，因为缺少真实 Developer ID 签名、公证和 stapling 后的 release 产物。
