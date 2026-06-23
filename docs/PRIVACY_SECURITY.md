# 隐私与安全说明

BLCaptain Codex Probe CLI 默认本地运行，不需要 OpenAI API Key，不需要登录 Codex，也不需要云端服务。

v0.4.0 新增「本地 Codex 会话级 Token 账本」。它仍然遵守同一个原则：

> 只处理用户显式提供的数据源；只保存 allowlist 字段；不读登录态、不读聊天正文、不上传云端。

## 数据来源

工具只处理以下来源：

| 数据源 | 说明 | 置信度上限 | 是否默认启用 |
|---|---|---|---|
| `official_export` | 用户显式提供的官方导出 CSV/JSON | exact | 否 |
| `snapshot_delta` | 用户显式提供的本地快照文件 | high | 否 |
| `local_status` | allowlist 字段形式的本地状态样本 | high | 否 |
| `desktop_visible` | 预留的桌面可见状态探测接口 | medium | 否 |
| `/status` 文本 | 用户粘贴或保存的 Codex `/status` 文本 | 任务级分析 | 否 |
| Skill / 输出文本 | 用户显式选择的 Skill、提示词或 AI 输出 | 质量体检 | 否 |

`sources doctor` 只做安全探测和边界说明，不读取聊天正文。

## 明确不做的事

- 不登录 OpenAI、ChatGPT 或 Codex。
- 不读取浏览器 cookie、系统凭据、钥匙串或 OpenAI token。
- 不抓包、不代理、不拦截、不修改 Codex 请求。
- 不读取聊天正文、prompt、assistant 输出或浏览器会话内容。
- 不扫描系统私密目录。
- 不上传报告、原文、数据库或统计到云端。
- 不自动安装、启用或修改 Skill。
- 不绕过登录、手机号验证、订阅、地区或官方计费。
- 不承诺省钱、无限额度、额度提升或替代官方 dashboard。

## 本地存储

默认数据库由用户通过 `--db` 指定，例如：

```bash
codex-probe --db .probe/ledger.db ledger init
```

会话级账本会保存：

- 数据源类型和启用状态。
- 会话 ID 或脱敏后的展示名。
- 项目名或项目 hash。
- token delta、credits delta、上下文峰值。
- 快照时间、数据源、置信度和脱敏证据摘要。
- 不含敏感原文的隐私审计日志。

它不会保存：

- 浏览器 cookie。
- OpenAI token。
- 钥匙串或系统凭据。
- 聊天正文。
- 完整私密路径。
- 真实 API key 或 Bearer token。

## 脱敏

报告和体检会尝试脱敏：

- OpenAI 风格 API key。
- `api_key`、`token`、`secret`、`access_token` 字段。
- Cookie 和 Bearer token。
- 邮箱和中国大陆手机号。
- 用户主目录等私密路径。

脱敏不是唯一安全边界。用户仍应避免把真实密钥、cookie 或生产数据放入输入文件。

## Watch 行为

`watch start` 必须由用户显式执行。

当前 P0 行为是记录 watcher 状态和用户意图，不默认后台读取聊天正文，也不自动扫描系统目录。后续如果接入更自动的数据源，也必须继续满足：

- 每个数据源单独开关。
- 只读取 allowlist 字段。
- 隐私页显示读取范围。
- 用户可以停止和删除本地业务数据。

## Dashboard 行为

`codex-probe dashboard` 当前生成本地 HTML 文件，例如：

```bash
codex-probe --db .probe/ledger.db dashboard --out reports/ledger/dashboard.html
```

它不会启动云端服务，也不会上传数据。HTML 页面只展示本地 SQLite 查询结果和脱敏后的示例字段。

## 删除

删除会话级账本业务数据：

```bash
codex-probe --db .probe/ledger.db delete --ledger --yes
```

删除旧版 `/status` 和 Skill 体检业务数据：

```bash
codex-probe --db .probe/demo.db delete --all --yes
```

删除后：

- 业务表中的会话、快照、delta、归因和报告索引会被清理。
- 审计日志会保留删除动作，用来证明删除发生。
- 审计日志不应包含 cookie、token、聊天正文或敏感原文。

## 发布前隐私检查

发布前必须扫描：

- API key。
- cookie。
- token。
- Bearer。
- GitHub token。
- 邮箱。
- 手机号。
- 用户私密路径。

不要提交：

- `.probe/`
- `reports/`
- `acceptance-artifacts/`
- 虚拟环境
- 数据库
- `.DS_Store`
- 临时截图
- 非本项目素材

## 风险声明

这是本地开源工具，不是官方账单系统。会话级数据是否精确，取决于用户显式提供的数据源。

- `exact` 可以用于精确归因。
- `high` 可以用于高可信分析。
- `medium` 和 `low` 只能作为估算，不应作为精确账单。

工具可以帮助你定位消耗、降低无意识长会话风险，但不能保证省钱，也不能突破官方额度或限制。
