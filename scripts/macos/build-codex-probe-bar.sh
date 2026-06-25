#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PACKAGE_DIR="$ROOT/desktop/macos/CodexProbeBar"
APP_DIR="$ROOT/build/CodexProbeBar.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
EXECUTABLE="$MACOS_DIR/CodexProbeBar"
CLI_PATH="${CODEX_PROBE_CLI:-}"

if [[ -z "$CLI_PATH" ]]; then
  if [[ -x "$ROOT/.venv/bin/codex-probe" ]]; then
    CLI_PATH="$ROOT/.venv/bin/codex-probe"
  elif command -v codex-probe >/dev/null 2>&1; then
    CLI_PATH="$(command -v codex-probe)"
  else
    CLI_PATH="codex-probe"
  fi
fi

swift build --package-path "$PACKAGE_DIR" -c release

install -d "$MACOS_DIR" "$RESOURCES_DIR"
install -m 755 "$PACKAGE_DIR/.build/release/CodexProbeBar" "$EXECUTABLE"

cat > "$CONTENTS_DIR/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDisplayName</key>
  <string>BLCaptain Codex Probe Bar</string>
  <key>CFBundleExecutable</key>
  <string>CodexProbeBar</string>
  <key>CFBundleIdentifier</key>
  <string>com.blcaptain.codexprobe.bar</string>
  <key>CFBundleName</key>
  <string>CodexProbeBar</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>0.9.0</string>
  <key>CFBundleVersion</key>
  <string>0.9.0</string>
  <key>LSMinimumSystemVersion</key>
  <string>13.0</string>
  <key>LSUIElement</key>
  <true/>
  <key>NSHumanReadableCopyright</key>
  <string>MIT License</string>
</dict>
</plist>
PLIST

cat > "$RESOURCES_DIR/defaults.json" <<JSON
{
  "cliPath": "$CLI_PATH",
  "dbPath": "$HOME/.codex-probe/probe.db",
  "reportsDir": "$HOME/CodexProbeReports/ledger",
  "range": "7d",
  "projectDir": "$ROOT"
}
JSON

echo "Built: $APP_DIR"
echo "CLI: $CLI_PATH"
echo "Reports: $HOME/CodexProbeReports/ledger"
