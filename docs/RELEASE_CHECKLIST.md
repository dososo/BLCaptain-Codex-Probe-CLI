# 发布前检查清单

发布 v0.9.0 前必须完成。

## 功能

- [x] `codex-probe --version` 返回 `0.9.0`。
- [x] `codex-probe ledger init` 可初始化本地账本。
- [x] `codex-probe sources doctor` 可输出安全数据源、最高置信度和隐私边界。
- [x] `codex-probe sources doctor --deep` 可安全检查本机 Codex 结构化数据源，只输出哈希、计数和字段覆盖率。
- [x] `codex-probe ledger inspect-export examples/ledger-samples/official-export.csv` 可识别 CSV 字段。
- [x] `codex-probe ledger inspect-export examples/ledger-samples/official-export.json` 可识别 JSON 字段。
- [x] `codex-probe ledger inspect-export examples/ledger-samples/official-export.jsonl` 可识别 JSONL 字段。
- [x] `codex-probe ledger map-export examples/ledger-samples/official-export-alt.json --out <mapping.json>` 可生成可编辑映射。
- [x] `codex-probe ledger import --official-export examples/ledger-samples/official-export.csv` 可导入 exact 样本。
- [x] `codex-probe ledger import --official-export examples/ledger-samples/official-export.jsonl` 可导入 JSONL 样本。
- [x] `codex-probe ledger import-history --dry-run --source local-codex` 可预览历史导入，不写入业务数据。
- [x] `codex-probe ledger import-history --source local-codex --root examples/ledger-samples/local-codex` 可导入 synthetic rollout 样本。
- [x] `codex-probe watch once` 可执行一次安全采集。
- [x] `codex-probe watch start/status/logs/stop` 可控制真实后台 watcher，并展示 PID、lock、最近采集时间、错误和采集次数。
- [x] `codex-probe setup --demo --no-open` 可完成初始化、dry-run、样本导入、报告生成和 Dashboard 生成。
- [x] `codex-probe watch status-page` 可生成友好的本地 watcher 状态页。
- [x] `codex-probe samples collect-rollout` 可生成只含白名单字段和哈希的脱敏校准样本。
- [x] `codex-probe sessions --range 7d` 可输出会话排行。
- [x] `codex-probe projects --range 30d` 可输出项目级聚合报告。
- [x] `codex-probe weekly-report --range 30d` 可输出 Codex 周报。
- [x] `codex-probe timeline --range 30d` 可输出阶段级高消耗时间线。
- [x] `codex-probe alerts --range 30d` 可输出本地预算与停止线预警。
- [x] `codex-probe task-report --range 30d` 可输出任务类型归因报告。
- [x] `codex-probe confidence-report` 可输出数据源可信度报告。
- [x] `swift build --package-path desktop/macos/CodexProbeBar` 可构建 macOS 状态栏 App。
- [x] `scripts/macos/build-codex-probe-bar.sh` 可生成 `build/CodexProbeBar.app`。
- [x] `scripts/macos/preflight-codex-probe-bar.sh` 可检查 `.app` bundle、`LSUIElement`、禁用 API、签名、公证和 Gatekeeper 状态。
- [x] `scripts/macos/package-codex-probe-bar.sh --skip-dmg` 可生成 release zip。
- [x] `scripts/macos/sign-codex-probe-bar.sh` 和 `scripts/macos/notarize-codex-probe-bar.sh` 已准备好维护者签名/公证流程，但不会在仓库内保存证书或凭据。
- [x] `codex-probe session-report <session_id>` 可输出单会话详情。
- [x] `codex-probe ledger-report --range 30d` 可输出总账报告。
- [x] `codex-probe privacy inspect` 可输出隐私审计报告。
- [x] `codex-probe dashboard` 可生成本地 HTML Dashboard，包含总览、排行、详情和隐私边界。
- [x] `codex-probe delete --watcher --yes` 可删除 watcher 状态和日志。
- [x] `codex-probe delete --ledger --yes` 可删除账本业务数据，并保留不含敏感原文的审计日志。
- [x] 旧版 `doctor`、`usage-report`、`skill-lint`、`delete --all --yes` 仍可用。

## 文档

- [x] README.md 已说明阶段级时间线、预算预警、任务归因、数据源可信度、项目级聚合、周报、轻安装方式、真实数据源接入、历史导入、watcher、隐私边界和旧版能力。
- [x] README.en.md 与中文 README 能力一致。
- [x] CHANGELOG.md 记录 v0.9.0。
- [x] docs/PRIVACY_SECURITY.md 说明 local Codex rollout allowlist、watcher、dashboard、删除和不可承诺边界。
- [x] docs/CODEX_DESKTOP_PROMPT.md 包含一句话入口：「请用 BLCaptain Codex Probe CLI 自动检查本地 Codex token 会话账本，导入可用历史记录，分析最近 7 天哪个会话消耗最多，并生成报告。」
- [x] docs/MACOS_WATCHER.md 说明 LaunchAgent 安装、卸载、状态、日志和隐私边界。
- [x] docs/SAMPLE_COLLECTION.md 说明脱敏 rollout 样本采集、输出字段和提交前检查。
- [x] docs/INSTALL.md 说明 Codex 桌面版、仓库脚本、uvx、pipx 和 Homebrew Formula 草案。
- [x] docs/MENUBAR_OR_DESKTOP_EVAL.md 说明菜单栏 App / 桌面组件评估和不读取登录态边界。
- [x] docs/MACOS_MENUBAR_APP.md 说明状态栏 App 构建、配置、使用和隐私边界。
- [x] docs/MACOS_MENUBAR_GOAL.md 保存可执行 `/goal` 和方案说明。
- [x] docs/MACOS_RELEASE_DISTRIBUTION.md 说明正式分发、Developer ID 签名、notarization、公证 stapling、Gatekeeper 验证和普通用户安装边界。
- [x] README 没有承诺省钱、无限额度、额度翻倍、绕登录、拼车、规避计费或替代官方 dashboard。

## 示例

- [x] `examples/ledger-samples/` 存在，并覆盖 CSV / JSON / JSONL / mapping / synthetic rollout / rollout variants / rollout stress。
- [x] `examples/reports/ledger/` 存在，并包含 sessions、session detail、ledger report、project summary、weekly report、timeline、alerts、source confidence、task report、privacy report 和 dashboard。
- [x] 示例不包含真实秘密、真实会话 ID、cookie、token、邮箱、手机号或用户私密路径。

## 测试

- [x] `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests` 通过。
- [x] `PYTHONDONTWRITEBYTECODE=1 python3 -m compileall src tests scripts/run_acceptance.py` 通过。
- [x] `PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_acceptance.py` 通过。
- [x] 端到端验收覆盖旧版 `/status`、新版 ledger、official export、local history、watcher 和删除链路。
- [x] 端到端验收覆盖 setup、watch status page 和 redacted rollout sample collection。
- [x] 端到端验收覆盖项目汇总、周报、阶段时间线、预警、任务归因、可信度和 rollout variant 样本。
- [x] HTML / JSON 报告契约测试覆盖 sessions、ledger-report、project summary、weekly report、timeline、alerts、task report、confidence report、privacy report 和 dashboard 核心结构。
- [x] Dashboard 或本地 HTML 页面经过截图或等价渲染校验：页面非空、中文可读、无明显遮挡、不展示敏感数据。
- [x] Dashboard 已支持项目、日期、置信度和模型筛选，并展示今日、本周、高风险会话、该停会话、预算预警、数据源可信度和任务归因。
- [x] macOS 状态栏 App 契约测试覆盖复用 CLI、禁用 Keychain/cookie/网络请求/抓包能力。
- [x] macOS 正式分发契约测试覆盖签名、公证、打包、preflight 脚本和凭据不落仓库。
- [x] 报告已说明 `credits` 不等同于官方账单金额，置信度和建议不替代官方 dashboard。
- [x] 会话排行已显示本机时区的具体开始/结束日期时间。

## 审计

- [x] `git status --short` 已检查，只提交本项目相关文件。
- [x] 不提交 `.probe/`、`reports/`、`acceptance-artifacts/`、虚拟环境、数据库、`.DS_Store`、临时截图和无关素材。
- [x] 已扫描 API key、cookie、token、Bearer、GitHub token、邮箱、手机号和用户私密路径。
- [x] 未提交 Apple ID、app-specific password、Developer ID 证书、私钥、notary 凭据或签名产物。
- [x] 已展示 staged 文件清单和敏感信息扫描结果。

## macOS 正式分发门槛

本地构建的 `build/CodexProbeBar.app` 默认未签名、未公证，只能作为 beta / 本地体验。

正式公开 release 前必须额外完成：

- [ ] 使用 Developer ID Application 证书运行 `scripts/macos/sign-codex-probe-bar.sh`。
- [ ] 使用 Apple notary service 运行 `scripts/macos/notarize-codex-probe-bar.sh`。
- [ ] 运行 `scripts/macos/preflight-codex-probe-bar.sh --require-signed --require-notarized` 并通过。
- [ ] 发布经过签名、公证和 stapling 的 zip / dmg。
- [ ] README release 文案不得把未签名构建描述为普通用户无摩擦正式安装包。

本地验收时间：2026-06-25。

证据目录：`acceptance-artifacts/20260625T115017Z/`。

安装 smoke：`python -m pip install .` 通过，安装后 `codex-probe --version` 返回 `codex-probe 0.9.0`；`setup --demo --no-open` 生成 sessions、ledger、project-summary、weekly、timeline、alerts、source-confidence、task-report、privacy、dashboard 和 watch-status 报告。
