# 发布前检查清单

发布 v0.4.0 前必须完成。

## 功能

- [x] `codex-probe --version` 返回 `0.4.0`。
- [x] `codex-probe ledger init` 可初始化本地账本。
- [x] `codex-probe sources doctor` 可输出安全数据源、最高置信度和隐私边界。
- [x] `codex-probe ledger import --official-export examples/ledger-samples/official-export.csv` 可导入 exact 样本。
- [x] `codex-probe ledger import --snapshot examples/ledger-samples/snapshot-delta.json` 可导入 high / medium / low 样本。
- [x] `codex-probe sessions --range 7d` 可输出会话排行。
- [x] `codex-probe session-report session_readme_release` 可输出单会话详情。
- [x] `codex-probe ledger-report --range 30d` 可输出总账报告。
- [x] `codex-probe privacy inspect` 可输出隐私审计报告。
- [x] `codex-probe dashboard` 可生成本地 HTML Dashboard。
- [x] `codex-probe delete --ledger --yes` 可删除账本业务数据，并保留不含敏感原文的审计日志。
- [x] 旧版 `doctor`、`usage-report`、`skill-lint`、`delete --all --yes` 仍可用。

## 文档

- [x] README.md 已说明会话级 Token 账本、三分钟示例、隐私边界和旧版能力。
- [x] README.en.md 与中文 README 能力一致。
- [x] CHANGELOG.md 记录 v0.4.0。
- [x] docs/PRIVACY_SECURITY.md 说明 ledger 数据源、watch、dashboard 和删除边界。
- [x] docs/CODEX_DESKTOP_PROMPT.md 包含一句话入口：「请用 BLCaptain Codex Probe CLI 打开本地 Codex token 会话账本，分析最近 7 天哪个会话消耗最多，并生成报告。」
- [x] README 没有承诺省钱、无限额度、额度翻倍、绕登录、拼车、规避计费或替代官方 dashboard。

## 示例

- [x] `examples/ledger-samples/` 存在，并覆盖 exact / high / medium / low 四类置信度。
- [x] `examples/reports/ledger/` 存在，并包含 sessions、session detail、ledger report、privacy report 和 dashboard。
- [x] 示例不包含真实秘密、真实会话 ID、cookie、token、邮箱、手机号或用户私密路径。

## 测试

- [x] `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests` 通过。
- [x] `PYTHONDONTWRITEBYTECODE=1 python3 -m compileall src tests scripts/run_acceptance.py` 通过。
- [x] `PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_acceptance.py` 通过。
- [x] 端到端验收覆盖旧版 `/status` 和新版 ledger 链路。
- [x] Dashboard 或本地 HTML 页面经过截图或等价渲染校验：页面非空、中文可读、无明显遮挡、不展示敏感数据。

## 审计

- [x] `git status --short` 已检查，只提交本项目相关文件。
- [x] 不提交 `.probe/`、`reports/`、`acceptance-artifacts/`、虚拟环境、数据库、`.DS_Store`、临时截图和无关素材。
- [x] 已扫描 API key、cookie、token、Bearer、GitHub token、邮箱、手机号和用户私密路径。
- [x] 已展示 staged 文件清单和敏感信息扫描结果。

本地验收时间：2026-06-23。

证据目录：`acceptance-artifacts/20260623T115715Z/`。

安装 smoke：`python -m pip install .` 通过，安装后 `codex-probe --version` 返回 `codex-probe 0.4.0`。
