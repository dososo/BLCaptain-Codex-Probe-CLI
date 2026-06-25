# macOS 状态栏 App /goal

## 目标分析

Codex Probe CLI 已经能生成会话账本、阶段时间线、预算预警、任务归因、数据源可信度和 Dashboard，但普通用户仍需要记命令、找报告路径、判断是否该刷新。macOS 状态栏 App 要解决的不是替代 CLI，而是把「当前是否危险、该不该停、报告在哪里」放到用户每天都会看的系统状态栏里。

适合第一版对外发布的形态：

- 原生 macOS 菜单栏 App，而不是 Electron 或网页壳。
- 状态栏常驻，点击弹出轻量控制面板。
- 通过 `codex-probe --json` 调用现有 CLI，不重复实现账本逻辑。
- 默认只读本地账本；用户主动点击时才执行 `watch once` 或生成 Dashboard。
- 面板首屏围绕用户痛点：最高消耗会话、token 总量、预警数、数据源可信度、下一步动作。
- 明确隐私边界：不登录、不读 cookie、不读 token、不读钥匙串、不抓包、不上传。

不建议第一版做的事：

- 不做登录态读取、浏览器注入、网络抓包、官方账单爬取。
- 不做复杂常驻后台采集守护，继续复用现有 CLI watcher。
- 不把菜单栏 App 做成完整 Dashboard；完整分析仍打开本地 HTML Dashboard。
- 不承诺官方账单级精确度或省钱效果。

## 推荐执行版（中文，可直接复制）

```text
/goal 基于当前 BLCaptain Codex Probe CLI，交付一个可对外发布的原生 macOS 状态栏 App 第一版，把 CLI 的会话账本、预算预警、数据源可信度和 Dashboard 入口变成普通用户可直接使用的桌面入口。

严格按 8 步流程执行：调研 → 分析 → 计划 → 开发 → 验证 → 测试 → 审计验收 → 总结。

目标：
1. 新增原生 macOS 菜单栏 App，名称为 BLCaptain Codex Probe Bar。
2. 状态栏展示简洁状态，点击后弹出美观、可读、非简陋的面板。
3. 面板展示：总 token、会话数、预警数、最高消耗会话、建议动作、预算预警、数据源可信度、隐私边界。
4. 面板提供常用动作：刷新、采集一次、生成/打开 Dashboard、打开报告目录、打开隐私报告、退出。
5. App 通过 `codex-probe --json` 调用现有 CLI，不重复实现 token 归因逻辑。
6. 支持环境变量或构建配置指定 CLI 路径、DB 路径、报告目录和时间范围；默认使用本地用户目录。
7. 提供构建脚本，把 Swift 可执行文件打包成 `.app`，并写入必要的 Info.plist 与默认配置。
8. 更新 README、README.en、macOS 文档和发布检查清单。

约束：
- local-first；不登录 OpenAI；不读取浏览器 cookie、OpenAI token、钥匙串、系统凭据；不抓包、不代理、不拦截、不上传。
- App 不直接读取聊天正文、prompt、assistant 输出或工具参数。
- 不伪造 token、credits、模型、会话 ID、置信度或建议。
- 不把菜单栏 App 做成另一个账本实现；核心计算必须复用 CLI。
- 不引入 Electron、React Native、外部付费 SDK 或网络服务。
- 不破坏现有 CLI 命令、JSON schema 和报告输出。
- 不提交 `.probe/`、根目录 `reports/`、`.venv/`、acceptance-artifacts、build/dist、本机临时、真实 `~/.codex` 原始数据、真实聊天内容、任何凭据或无关素材。

边界：
- 允许修改：`desktop/macos/`、`scripts/macos/`、`docs/`、`README.md`、`README.en.md`、`CHANGELOG.md`、`pyproject.toml`、`src/` 中必要版本信息、`tests/`、`tasks/todo.md`。
- 禁止修改：用户私有数据、浏览器目录、钥匙串、真实 `~/.codex` 原始文件、无关素材目录。

设计要求：
- 遵循 macOS 菜单栏工具最佳实践：状态栏轻量、面板信息密度适中、操作清晰、状态可解释。
- 首屏必须优先回答：现在是否高风险、哪个会话最贵、下一步该继续/降配/停止、数据是否可信。
- 视觉风格要克制、现代、工具型，不做营销页，不做空洞装饰。
- 文案必须面向普通用户，不要求用户理解 SQLite、JSON 或 CLI 参数。

开发步骤：
1. 调研：读取现有 CLI 命令、JSON 输出、报告路径、隐私文档和 macOS watcher 文档。
2. 分析：确定状态栏 App 最小可发布范围、数据流、配置方式和失败态。
3. 计划：写入 `tasks/todo.md` 的 macOS 状态栏 App 执行清单。
4. 开发：实现 Swift/AppKit 菜单栏 App、CLI Runner、状态面板、动作按钮、构建脚本和文档。
5. 验证：用 demo DB / demo 报告运行 App，确认能刷新、生成 Dashboard、打开报告目录。
6. 测试：运行 Python 单元测试、macOS App 静态契约测试、Swift build、compileall 和必要验收脚本。
7. 审计验收：扫描敏感信息和禁用能力；确认不包含 cookie/token/keychain/network 抓取逻辑；确认无私密路径和真实数据进入候选。
8. 总结：输出文件清单、运行方式、测试结果、审计结果、是否建议公开 beta，以及剩余风险。

验证命令：
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m compileall src tests scripts/run_acceptance.py`
- `swift build --package-path desktop/macos/CodexProbeBar`
- `scripts/macos/build-codex-probe-bar.sh`
- 运行生成的 App 或 Swift 可执行文件，至少完成一次刷新和打开 Dashboard。

完成条件：
- macOS 状态栏 App 可构建、可启动、可调用本地 CLI 并展示真实本地报告摘要。
- README 和 macOS 文档能让普通用户知道如何安装、启动、刷新、打开 Dashboard 和理解隐私边界。
- 测试和审计通过，未发现真实敏感信息或越界读取能力。

暂停条件：
- 需要 Apple Developer 账号签名、公证、上架、付费服务、登录态、生产数据、浏览器 cookie、OpenAI token、钥匙串权限、网络抓包或破坏性操作时暂停并说明。
```

## Goal Draft (English-compatible)

```text
/goal Build a release-quality first version of a native macOS menu bar app for BLCaptain Codex Probe CLI. The app should expose the existing local session ledger, budget alerts, source confidence, and dashboard entry points as a user-friendly desktop status-bar experience.
Process: follow the 8-step flow exactly: research -> analysis -> plan -> development -> verification -> testing -> audit acceptance -> summary.
Verification: run Python tests, compileall, Swift build, the macOS bundle build script, and at least one local demo refresh/open-dashboard workflow.
Constraints: local-first only; do not log in, read browser cookies, OpenAI tokens, keychains, system credentials, chat content, prompts, assistant outputs, packet captures, proxies, or upload data. Reuse the CLI JSON commands for all core calculations.
Boundaries: write only desktop/macos, scripts/macos, docs, README files, CHANGELOG, version metadata if needed, tests, and tasks/todo.md. Do not submit private data, .probe, reports, venvs, acceptance artifacts, build output, raw ~/.codex files, credentials, or unrelated assets.
Completion: the app builds, launches, shows local usage summary and alerts, provides refresh/run-once/open-dashboard/open-reports actions, documents privacy boundaries, and passes tests/audit.
Pause if: signing/notarization accounts, paid services, login state, production data, cookies, tokens, keychain access, packet capture, destructive operations, or ambiguous ownership are required.
```
