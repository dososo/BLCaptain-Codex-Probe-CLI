# Codex Usage Skill Probe

本项目是一个本地只读 CLI 探针，用于验证两个 P0 工作流：

1. 任务级 Token/额度用量自查：解释为什么贵、怎么降配、什么时候该停。
2. Skill/输出质量体检：少装错插件，识别 AI 味、插件风险和缺失验收。

产品口径是 **Watch / 验证型 v0.1**，不是商业化 Go 产品。它不替代 OpenAI 官方 usage dashboard 或 `/status`，不承诺省钱、额度翻倍、无限额度或真人伪装。

## 安装

需要 Python 3.10 或更高版本。

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
```

安装后可使用两个等价命令：

```bash
probe --version
codex-usage-skill-probe --version
```

## 快速开始

导入 `/status` 文本：

```bash
probe --db .probe/demo.db import --status examples/status.txt --goal "生成交付报告"
```

生成任务级用量报告：

```bash
probe --db .probe/demo.db usage-report --budget-tokens 100000 --out reports/usage-report.md
```

体检 Skill 或输出文本：

```bash
probe --db .probe/demo.db skill-lint examples/risky-skill.md --out reports/skill-lint-report.md
```

删除本地业务数据：

```bash
probe --db .probe/demo.db delete --all --yes
```

删除后再次生成用量报告应返回 `NO_USAGE_DATA`。

## 命令

| 命令 | 作用 |
|---|---|
| `probe import --status <file>` | 导入用户显式提供的 `/status` 文本 |
| `probe import --manual-json <file>` | 导入手工 JSON 用量样本 |
| `probe usage-report` | 生成任务级用量自查报告 |
| `probe skill-lint <file>` | 生成 Skill/输出体检报告 |
| `probe delete --all --yes` | 删除本地业务数据，保留最小审计日志 |

## 示例数据

- `examples/status.txt`：包含模型、模式、token、credits、剩余额度的文本样本。
- `examples/manual-usage.json`：手工 JSON 用量样本。
- `examples/risky-skill.md`：包含 AI 味、插件风险和密钥样例的风险文本。
- `examples/clean-skill.md`：相对安全的 Skill 样例。

示例中的密钥是无效假数据；报告会脱敏常见 API key、token、cookie、邮箱和手机号。

## 验收

开发者可直接在源码环境运行自动化测试：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m compileall src tests scripts/run_acceptance.py
```

运行端到端验收脚本：

```bash
python3 scripts/run_acceptance.py
```

验收脚本会保存命令、stdout、stderr 和报告路径到 `acceptance-artifacts/`。

本地验收证据：

```text
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
.....
Ran 5 tests in 0.195s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall src tests scripts/run_acceptance.py
Listing 'src'...
Listing 'src/codex_usage_skill_probe'...
Listing 'tests'...
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_acceptance.py
acceptance passed: acceptance-artifacts/20260620T055431Z
```

`acceptance-artifacts/20260620T055431Z/commands.md` 记录了 5 个端到端步骤：导入 `/status`、生成任务级用量报告、生成 Skill 体检报告、删除本地业务数据、删除后返回 `NO_USAGE_DATA`。

安装 smoke 已用 `.venv-verify` 和普通本地安装验证：

```text
python -m pip install .
probe 0.1.0
{
  "ok": true,
  "parsed_count": 1,
  "status": "ok"
}
```

## 安全边界

本工具只读取用户显式提供的本地文件或文本。它不会：

- 登录 OpenAI 或 Codex。
- 代理、拦截或修改 Codex 请求。
- 读取浏览器 cookie、token 或系统凭据。
- 绕过登录、手机号、订阅、地区或官方计费。
- 上传数据到云端。
- 自动安装、启用或修改 Skill。

详见 [隐私与安全说明](docs/PRIVACY_SECURITY.md)。

## 开源发布状态

当前版本目标是 v0.1 本地 CLI，可用于真实用户验证，不是演示页。发布前检查清单见 [发布前检查清单](docs/RELEASE_CHECKLIST.md)。

`.gitignore` 已排除虚拟环境、Python 缓存、本地数据库、构建产物和验收产物。`acceptance-artifacts/` 仅作为本机验收证据，不应随源码发布。

## 许可证

MIT，见 [LICENSE](LICENSE)。
