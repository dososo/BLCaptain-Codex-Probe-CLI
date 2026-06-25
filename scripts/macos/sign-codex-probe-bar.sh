#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_DIR="${1:-$ROOT/build/CodexProbeBar.app}"
IDENTITY="${DEVELOPER_ID_APPLICATION:-}"

if [[ ! -d "$APP_DIR" ]]; then
  echo "App bundle not found: $APP_DIR" >&2
  echo "Run scripts/macos/build-codex-probe-bar.sh first." >&2
  exit 2
fi

if [[ -z "$IDENTITY" ]]; then
  echo "Missing DEVELOPER_ID_APPLICATION." >&2
  echo "Example: DEVELOPER_ID_APPLICATION='Developer ID Application: Your Name (TEAMID)' scripts/macos/sign-codex-probe-bar.sh" >&2
  exit 2
fi

codesign \
  --force \
  --timestamp \
  --options runtime \
  --sign "$IDENTITY" \
  "$APP_DIR"

codesign --verify --deep --strict --verbose=2 "$APP_DIR"
codesign -dv "$APP_DIR" 2>&1

echo "Signed and verified: $APP_DIR"
