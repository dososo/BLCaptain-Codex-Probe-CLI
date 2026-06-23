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
