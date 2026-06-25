# macOS 正式分发、签名与公证

本文档用于回答一个发布前必须讲清楚的问题：BLCaptain Codex Probe Bar 是否已经符合普通 macOS 用户「下载后能顺利打开」的标准。

## 当前结论

当前仓库可以构建本地 `.app`，适合开发者、本地验证和公开 beta 体验；但如果没有 Apple Developer ID 签名、notarization 公证和 stapling，不能承诺普通用户从 GitHub 下载后完全无 Gatekeeper 提示。

要达到正式对外分发标准，必须完成：

- 使用 Apple Developer ID Application 证书签名。
- 开启 hardened runtime。
- 提交 Apple notary service 公证。
- 对 `.app` 或 `.dmg` 执行 stapling。
- 用 `spctl` 验证 Gatekeeper。
- 发布签名并公证后的 zip / dmg，而不是让普通用户自己运行源码构建。

本仓库已经补齐对应脚本和 preflight 检查，但真正签名/公证需要维护者自己的 Apple Developer 账号、证书和 app-specific password。仓库不会、也不应该提交这些凭据。

## 发布流水线

本地构建：

```bash
scripts/macos/build-codex-probe-bar.sh
```

发布前检查：

```bash
scripts/macos/preflight-codex-probe-bar.sh
```

签名：

```bash
DEVELOPER_ID_APPLICATION="Developer ID Application: Your Name (TEAMID)" \
  scripts/macos/sign-codex-probe-bar.sh
```

公证：

```bash
APPLE_ID="APPLE_ID_ACCOUNT" \
APPLE_TEAM_ID="TEAMID" \
APPLE_APP_SPECIFIC_PASSWORD="APP_SPECIFIC_PASSWORD" \
  scripts/macos/notarize-codex-probe-bar.sh
```

打包：

```bash
scripts/macos/package-codex-probe-bar.sh
```

正式发布门槛检查：

```bash
scripts/macos/preflight-codex-probe-bar.sh --require-signed --require-notarized
```

## 普通用户体验标准

达到正式分发标准后，普通用户预期流程应该是：

1. 下载 release 中的 `CodexProbeBar-vX.Y.Z.dmg` 或 `.zip`。
2. 双击打开，不出现「无法验证开发者」或需要命令行绕过 Gatekeeper 的提示。
3. 首次打开只看到正常 macOS 安全确认。
4. 状态栏出现 BLCaptain Codex Probe Bar。
5. 用户点击刷新或生成 Dashboard 时，只调用本地 `codex-probe`。

如果没有签名和公证，README 必须把入口描述为「本地构建体验」或「公开 beta」，不能写成无摩擦正式安装。

## 权限与隐私边界

状态栏 App 当前不申请额外系统权限。它只调用本地 CLI，不包含：

- Keychain / 钥匙串读取。
- 浏览器 cookie 读取。
- OpenAI token 读取。
- `URLSession` 网络上传。
- `WKWebView` 登录态读取。
- 抓包、代理、请求拦截。
- 辅助功能事件监听。

preflight 脚本会扫描这些禁用能力。如果未来引入自动更新、登录项或偏好设置，需要重新做权限、签名、隐私和用户提示审计。

## 可执行 /goal 提示词

```text
/goal 基于当前 BLCaptain Codex Probe CLI 和已实现的 BLCaptain Codex Probe Bar，完成 macOS 正式分发工程加固，目标是让维护者能够产出符合普通 macOS 用户下载体验的签名、公证、可验证 release 包。

严格按 8 步执行：调研 → 分析 → 计划 → 开发 → 验证 → 测试 → 审计验收 → 总结。

目标：
1. 审计现有 macOS 状态栏 App 是否符合 macOS 状态栏工具、签名、公证、Gatekeeper 和隐私边界要求。
2. 明确区分本地 beta 构建和正式签名公证 release。
3. 新增签名脚本、公证脚本、打包脚本和 preflight 脚本。
4. 文档说明普通用户无摩擦安装所需条件、维护者 release 流程、必要环境变量和失败排查。
5. 测试覆盖脚本存在性、关键命令、禁用敏感能力和凭据不落仓库。

约束：
- 不提交 Apple ID、app-specific password、Developer ID 证书、私钥、notary 凭据或任何系统凭据。
- 不读取浏览器 cookie、OpenAI token、钥匙串、系统凭据、聊天正文或真实 ~/.codex 原始数据。
- 不绕过 Gatekeeper，不教用户关闭安全机制，不把未签名版本包装成正式发行版。
- 不引入网络服务、自动更新框架或安装器，除非有明确测试和隐私审计。
- 不提交 build、dist、.probe、reports、.venv、acceptance-artifacts 或无关素材。

验证：
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m compileall src tests scripts/run_acceptance.py`
- `swift build --package-path desktop/macos/CodexProbeBar`
- `scripts/macos/build-codex-probe-bar.sh`
- `scripts/macos/preflight-codex-probe-bar.sh`
- `scripts/macos/package-codex-probe-bar.sh --skip-dmg`

完成条件：
- 本地未签名构建的风险被明确标注。
- 维护者有清晰命令完成签名、公证、stapling、Gatekeeper 验证和打包。
- preflight 能识别未签名/未公证状态，并可在正式发布模式下失败。
- 测试和审计通过，未发现凭据、隐私越界能力或误导性文案。

暂停条件：
- 需要真实 Apple Developer 账号操作、证书私钥、notary 凭据、付费服务、生产分发账号、真实用户数据或破坏性操作时暂停并说明。
```

## 参考

- Apple 官方文档：Notarizing macOS software before distribution  
  https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution
- Apple 官方文档：Hardened Runtime  
  https://developer.apple.com/documentation/security/hardened-runtime
- Apple 官方文档：Distributing your app for beta testing and releases  
  https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases
