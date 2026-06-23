#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DB_PATH="${DB_PATH:-$ROOT_DIR/.probe/probe.db}"
INTERVAL_SECONDS="${INTERVAL_SECONDS:-60}"
CODEX_ROOT="${CODEX_ROOT:-}"
LIMIT_FILES="${LIMIT_FILES:-}"
LABEL="com.blcaptain.codex-probe.watch"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_DIR="$ROOT_DIR/.probe/watch"

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR" "$ROOT_DIR/.probe"

EXTRA_ARGS=""
if [[ -n "$CODEX_ROOT" ]]; then
  EXTRA_ARGS="$EXTRA_ARGS
    <string>--root</string>
    <string>$CODEX_ROOT</string>"
fi
if [[ -n "$LIMIT_FILES" ]]; then
  EXTRA_ARGS="$EXTRA_ARGS
    <string>--limit-files</string>
    <string>$LIMIT_FILES</string>"
fi

cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>WorkingDirectory</key>
  <string>$ROOT_DIR</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON_BIN</string>
    <string>-m</string>
    <string>codex_usage_skill_probe</string>
    <string>--db</string>
    <string>$DB_PATH</string>
    <string>--json</string>
    <string>watch</string>
    <string>_run</string>
    <string>--interval-seconds</string>
    <string>$INTERVAL_SECONDS</string>
$EXTRA_ARGS
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <false/>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/launchagent.out.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/launchagent.err.log</string>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)" "$PLIST" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl kickstart -k "gui/$(id -u)/$LABEL"

echo "Installed $LABEL"
echo "Plist: $PLIST"
echo "DB: $DB_PATH"
if [[ -n "$CODEX_ROOT" ]]; then
  echo "Codex root: $CODEX_ROOT"
fi
echo "Logs: $LOG_DIR"
