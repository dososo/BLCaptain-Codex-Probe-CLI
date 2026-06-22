# 发布前检查清单

发布 v0.3 前必须完成。

- [x] README 包含安装、快速开始、命令说明、安全边界和验收命令。
- [x] LICENSE 存在。
- [x] CHANGELOG 记录版本变化。
- [x] `examples/` 不包含真实秘密。
- [x] `PYTHONPATH=src python3 -m unittest discover -s tests` 通过。
- [x] `python3 -m compileall src tests scripts/run_acceptance.py` 通过。
- [x] `python3 scripts/run_acceptance.py` 通过。
- [x] 端到端验收覆盖导入用量、生成用量报告、生成 Skill 体检、删除数据、删除后返回 `NO_USAGE_DATA`。
- [x] 报告不泄露完整 API key、cookie、token、邮箱或手机号。
- [x] CI 配置存在并运行测试。
- [x] 文案没有承诺省钱、无限额度、额度翻倍、绕登录、拼车、规避计费或替代官方 dashboard。

本地验收时间：2026-06-20。

证据目录：`acceptance-artifacts/20260622T094640Z/`。

安装 smoke：`.venv-release/bin/python -m pip install .` 通过，`.venv-release/bin/codex-probe --version` 返回 `codex-probe 0.3.0`，安装后导入、报告、删除链路已通过。
