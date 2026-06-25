# 安装方式

BLCaptain Codex Probe CLI 是本地优先工具。安装方式可以轻，但边界不能变：不登录 OpenAI，不读取浏览器 cookie，不读取 token、钥匙串或系统凭据，不上传任何数据。

## Codex 桌面版安装

最适合普通用户的方式，是在 Codex 桌面版打开一个空目录，然后说：

```text
帮我安装这个仓库 https://github.com/dososo/BLCaptain-Codex-Probe-CLI。
安装完成后先运行安全 demo，只使用仓库示例数据生成 Codex 用量 Dashboard。
不要读取我的真实 Codex 历史、浏览器 cookie、token、钥匙串或系统凭据，不上传任何数据。
```

Codex 会完成 clone、创建本地虚拟环境、安装 CLI、运行 demo，并告诉你 Dashboard 路径。

## 仓库本地脚本

```bash
git clone https://github.com/dososo/BLCaptain-Codex-Probe-CLI.git
cd BLCaptain-Codex-Probe-CLI
scripts/setup-local.sh
```

无参数时会运行安全 demo，只使用仓库 synthetic 样本。

## macOS 状态栏 App

CLI 安装完成后，可以构建原生状态栏 App：

```bash
scripts/macos/build-codex-probe-bar.sh
open build/CodexProbeBar.app
```

它会优先使用当前仓库 `.venv/bin/codex-probe`，并把报告写到 `~/CodexProbeReports/ledger`。详细配置见 [macOS 状态栏 App](MACOS_MENUBAR_APP.md)。

这条路径是本地体验版。普通用户正式下载使用时，维护者应发布经过 Developer ID 签名、Apple notarization 公证和 stapling 的 zip / dmg。对应发布流程见 [macOS 正式分发、签名与公证](MACOS_RELEASE_DISTRIBUTION.md)。

## uvx

正式发布到 PyPI 后，推荐：

```bash
uvx blcaptain-codex-probe --version
uvx blcaptain-codex-probe setup --demo
```

如果正在本地开发或验证 GitHub 版本，可以先 clone 仓库，再用：

```bash
uvx --from . codex-probe setup --demo
```

说明：`uvx --from .` 依赖当前目录的 `pyproject.toml`，适合本地验证；公开用户路径应等待 PyPI 包发布后再使用包名。

## pipx

正式发布到 PyPI 后：

```bash
pipx install blcaptain-codex-probe
codex-probe setup --demo
```

本地仓库验证：

```bash
pipx install .
codex-probe setup --demo
```

## Homebrew Formula 草案

当前尚未发布 Homebrew tap，不应写成已经可用。下面只是发布准备草案：

```ruby
class BlcaptainCodexProbe < Formula
  include Language::Python::Virtualenv

  desc "Local-first Codex session token ledger and Skill inspection CLI"
  homepage "https://github.com/dososo/BLCaptain-Codex-Probe-CLI"
  url "https://github.com/dososo/BLCaptain-Codex-Probe-CLI/archive/refs/tags/v0.9.0.tar.gz"
  sha256 "REPLACE_WITH_RELEASE_TARBALL_SHA256"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    system bin/"codex-probe", "--version"
  end
end
```

发布 Homebrew 版本前必须完成：

- 创建正式 GitHub release tag。
- 计算 release tarball sha256。
- 验证 `brew install --build-from-source`。
- 明确 README 中 Homebrew 仍不读取登录态、cookie、token、钥匙串或系统凭据。

## 验证安装

安装后至少运行：

```bash
codex-probe --version
codex-probe setup --demo --no-open
```

如果只想检查本机可用数据源：

```bash
codex-probe sources doctor
codex-probe sources doctor --deep
```

`--deep` 也只输出哈希、计数和字段覆盖率，不输出聊天正文或完整私密路径。
