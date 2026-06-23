# 隐私与安全说明

BLCaptain Codex Probe CLI 默认本地运行，不需要 OpenAI API Key，不需要登录 Codex，也不需要云端服务。

v0.6.0 新增一键 setup、Dashboard 筛选、watcher 状态页和脱敏 rollout 样本采集。它仍然遵守同一个原则：

> 只处理用户显式提供或显式启用的数据源；只保存 allowlist 字段；不读登录态、不读聊天正文、不上传云端。

## 数据来源

工具只处理以下来源：

| 数据源 | 说明 | 置信度上限 | 是否默认启用 |
|---|---|---|---|
| `official_export` | 用户显式提供的官方导出 CSV/JSON/JSONL | exact | 否 |
| `snapshot_delta` | 用户显式提供的本地快照文件 | high | 否 |
| `local_codex_rollout` | 本机 Codex rollout JSONL 中的 token 用量白名单字段 | high | 否 |
| `local_status` | allowlist 字段形式的本地状态样本 | high | 否 |
| `desktop_visible` | 预留的桌面可见状态探测接口 | medium | 否 |
| `/status` 文本 | 用户粘贴或保存的 Codex `/status` 文本 | 任务级分析 | 否 |
| Skill / 输出文本 | 用户显式选择的 Skill、提示词或 AI 输出 | 质量体检 | 否 |

`sources doctor` 只做安全探测和边界说明，不读取聊天正文。`sources doctor --deep` 会扫描本机 Codex rollout 文件，但只输出哈希、计数、mtime 和字段覆盖率，不输出完整路径、prompt、assistant 输出或工具参数。

## 明确不做的事

- 不登录 OpenAI、ChatGPT 或 Codex。
- 不读取浏览器 cookie、系统凭据、钥匙串或 OpenAI token。
- 不抓包、不代理、不拦截、不修改 Codex 请求。
- 不读取聊天正文、prompt、assistant 输出或浏览器会话内容。
- 不扫描系统私密目录；本地历史导入只在 Codex 数据目录或用户显式指定目录内查找 `rollout-*.jsonl`。
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
- 项目名或项目 hash。local history 默认使用项目 hash，不展示完整路径。
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

## Local History 行为

`ledger import-history --source local-codex` 会查找 Codex rollout JSONL，并且只处理包含以下标记的结构化用量行：

- `last_token_usage`
- `total_token_usage`
- `rate_limits`

读取和保存的字段限定为：

- 时间戳。
- 会话 ID 派生 hash。
- turn id。
- 模型名。
- token 数字。
- credits 数字。
- 上下文窗口数字。
- 项目路径 hash。
- 文件 hash 和行号形式的 `raw_ref`。

它会跳过包含 `response_item`、正文 `content`、工具 `arguments` 等标记的行。即使 JSONL 文件中存在聊天正文，本工具也不会把正文解析进账本或报告。

如果本地日志没有 token 字段，工具只能报告不可导入或只保留元信息；不会伪造会话 token。

## Watch 行为

`watch start` 必须由用户显式执行。

v0.6.0 的 watcher 是真实后台进程，会记录：

- PID。
- 状态文件。
- lock 文件。
- 最近采集时间。
- 采集次数。
- 最近错误。
- 日志路径。

它调用同一套 local history 白名单读取逻辑，不默认读取聊天正文，也不自动读取浏览器、cookie、token、钥匙串或系统凭据。

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

删除 watcher 状态和日志：

```bash
codex-probe --db .probe/ledger.db delete --watcher --yes
```

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

## credits、置信度和建议的口径

- `credits` 只表示数据源提供的 credits / cost / quota 数值，不等同于美元、人民币或官方账单金额。
- `credits delta` 只在同一数据源、同一口径可解释为消耗差值时展示；无法确认口径时显示为 `未知`。
- `exact` 只用于用户显式提供的官方导出或等价结构化数据直接给出会话级 token 字段。
- `high` 表示本地结构化记录能稳定关联会话和 token 字段，但仍不是官方账单。
- `medium` 和 `low` 只能作为治理参考，不能作为精确账单或费用凭证。
- `建议` 是基于 token delta 阈值的治理动作：`>=100,000` 建议停止，`>=50,000` 建议降配或拆分，低于阈值建议继续观察。
- 报告里的日期时间按当前系统时区展示。中国大陆系统通常显示为 `UTC+08:00`。
