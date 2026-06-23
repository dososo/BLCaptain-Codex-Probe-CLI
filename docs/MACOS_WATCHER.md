# macOS Watcher 入口

v0.6.0 提供一个轻量 LaunchAgent 入口和本地状态页，用来在 macOS 登录会话里启动并查看 watcher。它不是菜单栏 App，也不会登录 OpenAI、读取浏览器 cookie、读取 token、读取钥匙串或上传数据。

## 安装前

先确认 CLI 能运行：

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
codex-probe --version
```

## 安装 LaunchAgent

体验模式，只读取仓库内 synthetic rollout 样本：

```bash
PYTHON_BIN="$(pwd)/.venv/bin/python" \
DB_PATH="$(pwd)/.probe/launchagent-demo.db" \
CODEX_ROOT="$(pwd)/examples/ledger-samples/local-codex" \
INTERVAL_SECONDS=10 \
scripts/macos/install-watcher-launchagent.sh
```

真实模式，读取默认 Codex 数据目录：

```bash
PYTHON_BIN="$(pwd)/.venv/bin/python" \
DB_PATH="$(pwd)/.probe/probe.db" \
INTERVAL_SECONDS=60 \
scripts/macos/install-watcher-launchagent.sh
```

安装后会写入：

- `~/Library/LaunchAgents/com.blcaptain.codex-probe.watch.plist`
- `.probe/watch/status.json`
- `.probe/watch/watch.log`
- `.probe/watch/launchagent.out.log`
- `.probe/watch/launchagent.err.log`

## 查看状态

```bash
codex-probe --db .probe/probe.db watch status
codex-probe --db .probe/probe.db watch logs
codex-probe --db .probe/probe.db watch status-page --open
codex-probe --db .probe/probe.db sessions --range 7d
```

`watch status-page` 会生成本地 HTML 状态页，展示 watcher 状态、最近日志和最近会话排行。它不启动服务，也不上传数据。

## 停止和卸载

```bash
codex-probe --db .probe/probe.db watch stop
scripts/macos/uninstall-watcher-launchagent.sh
codex-probe --db .probe/probe.db delete --watcher --yes
```

## 隐私边界

- watcher 只调用 `ledger import-history --source local-codex` 同等的白名单读取逻辑。
- 只读取 token 用量字段、时间、模型、turn id、会话 id 派生哈希和路径哈希。
- 不保存聊天正文、prompt、assistant 输出、工具参数、完整私密路径、cookie、token、钥匙串或系统凭据。
- 如果本机 Codex 日志没有 token 字段，watcher 只能记录没有可导入数据，不会伪造用量。
