#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PACKAGE_DIR="$ROOT/desktop/macos/CodexProbeBar"
APP_SUPPORT="$HOME/Library/Application Support/BLCaptain Codex Probe"
APP_DIR="${CODEX_PROBE_APP_DIR:-$HOME/Applications/CodexProbeBar.app}"
STAGING_APP="$APP_DIR.staging.$$"
CONTENTS_DIR="$STAGING_APP/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
EXECUTABLE="$MACOS_DIR/CodexProbeBar"
CLI_PATH="${CODEX_PROBE_CLI:-}"

if [[ -z "$CLI_PATH" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    install -d "$APP_SUPPORT"
    if [[ ! -x "$APP_SUPPORT/.venv/bin/python" ]]; then
      python3 -m venv "$APP_SUPPORT/.venv"
    fi
    PIP_DISABLE_PIP_VERSION_CHECK=1 "$APP_SUPPORT/.venv/bin/python" -m pip install --quiet "$ROOT"
    CLI_PATH="$APP_SUPPORT/.venv/bin/codex-probe"
  elif [[ -x "$ROOT/.venv/bin/codex-probe" ]]; then
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
  <string>0.9.1</string>
  <key>CFBundleVersion</key>
  <string>0.9.1</string>
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
  "dbPath": "$APP_SUPPORT/codex-probe-bar.db",
  "reportsDir": "$APP_SUPPORT/Reports",
  "range": "7d",
  "projectDir": "$APP_SUPPORT"
}
JSON

xattr -cr "$APP_DIR" 2>/dev/null || true
xattr -cr "$STAGING_APP" 2>/dev/null || true
codesign --force --deep --sign - "$STAGING_APP"

if [[ -d "$APP_DIR" ]]; then
  PREVIOUS_APP="$(dirname "$APP_DIR")/CodexProbeBar.previous.$(date +%Y%m%d%H%M%S).app"
  mv "$APP_DIR" "$PREVIOUS_APP"
  echo "Previous build moved to: $PREVIOUS_APP"
fi
mv "$STAGING_APP" "$APP_DIR"
xattr -d com.apple.FinderInfo "$APP_DIR" 2>/dev/null || true
xattr -d 'com.apple.fileprovider.fpfs#P' "$APP_DIR" 2>/dev/null || true
codesign --verify --deep --strict --verbose=2 "$APP_DIR"

echo "Built: $APP_DIR"
echo "CLI: $CLI_PATH"
echo "Reports: $APP_SUPPORT/Reports"
echo "Signature: ad-hoc local bundle signature"
