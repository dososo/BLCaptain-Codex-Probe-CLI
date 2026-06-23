#!/usr/bin/env bash
set -euo pipefail

LABEL="com.blcaptain.codex-probe.watch"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

launchctl bootout "gui/$(id -u)" "$PLIST" >/dev/null 2>&1 || true

if [[ -f "$PLIST" ]]; then
  rm "$PLIST"
fi

echo "Uninstalled $LABEL"
