# 发布前检查清单

发布 v0.6.0 前必须完成。

## 功能

- [x] `codex-probe --version` 返回 `0.6.0`。
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
- [x] `codex-probe session-report <session_id>` 可输出单会话详情。
- [x] `codex-probe ledger-report --range 30d` 可输出总账报告。
- [x] `codex-probe privacy inspect` 可输出隐私审计报告。
- [x] `codex-probe dashboard` 可生成本地 HTML Dashboard，包含总览、排行、详情和隐私边界。
- [x] `codex-probe delete --watcher --yes` 可删除 watcher 状态和日志。
- [x] `codex-probe delete --ledger --yes` 可删除账本业务数据，并保留不含敏感原文的审计日志。
- [x] 旧版 `doctor`、`usage-report`、`skill-lint`、`delete --all --yes` 仍可用。

## 文档

- [x] README.md 已说明真实数据源接入、历史导入、watcher、macOS 入口、隐私边界和旧版能力。
- [x] README.en.md 与中文 README 能力一致。
- [x] CHANGELOG.md 记录 v0.6.0。
- [x] docs/PRIVACY_SECURITY.md 说明 local Codex rollout allowlist、watcher、dashboard、删除和不可承诺边界。
- [x] docs/CODEX_DESKTOP_PROMPT.md 包含一句话入口：「请用 BLCaptain Codex Probe CLI 自动检查本地 Codex token 会话账本，导入可用历史记录，分析最近 7 天哪个会话消耗最多，并生成报告。」
- [x] docs/MACOS_WATCHER.md 说明 LaunchAgent 安装、卸载、状态、日志和隐私边界。
- [x] docs/SAMPLE_COLLECTION.md 说明脱敏 rollout 样本采集、输出字段和提交前检查。
- [x] README 没有承诺省钱、无限额度、额度翻倍、绕登录、拼车、规避计费或替代官方 dashboard。

## 示例

- [x] `examples/ledger-samples/` 存在，并覆盖 CSV / JSON / JSONL / mapping / synthetic rollout。
- [x] `examples/reports/ledger/` 存在，并包含 sessions、session detail、ledger report、privacy report 和 dashboard。
- [x] 示例不包含真实秘密、真实会话 ID、cookie、token、邮箱、手机号或用户私密路径。

## 测试

- [x] `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests` 通过。
- [x] `PYTHONDONTWRITEBYTECODE=1 python3 -m compileall src tests scripts/run_acceptance.py` 通过。
- [x] `PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_acceptance.py` 通过。
- [x] 端到端验收覆盖旧版 `/status`、新版 ledger、official export、local history、watcher 和删除链路。
- [x] 端到端验收覆盖 setup、watch status page 和 redacted rollout sample collection。
- [x] Dashboard 或本地 HTML 页面经过截图或等价渲染校验：页面非空、中文可读、无明显遮挡、不展示敏感数据。
- [x] Dashboard 已支持项目、日期、置信度和模型筛选。
- [x] 报告已说明 `credits` 不等同于官方账单金额，置信度和建议不替代官方 dashboard。
- [x] 会话排行已显示本机时区的具体开始/结束日期时间。

## 审计

- [x] `git status --short` 已检查，只提交本项目相关文件。
- [x] 不提交 `.probe/`、`reports/`、`acceptance-artifacts/`、虚拟环境、数据库、`.DS_Store`、临时截图和无关素材。
- [x] 已扫描 API key、cookie、token、Bearer、GitHub token、邮箱、手机号和用户私密路径。
- [x] 已展示 staged 文件清单和敏感信息扫描结果。

本地验收时间：2026-06-23。

证据目录：`acceptance-artifacts/20260623T124957Z/`。

安装 smoke：`python -m pip install .` 通过，安装后 `codex-probe --version` 返回 `codex-probe 0.6.0`。
