#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_DIR="${CODEX_PROBE_APP_DIR:-$HOME/Applications/CodexProbeBar.app}"
DIST_DIR="$ROOT/dist"
VERSION="0.9.1"
ZIP_PATH="$DIST_DIR/CodexProbeBar-v$VERSION.zip"
DMG_PATH="$DIST_DIR/CodexProbeBar-v$VERSION.dmg"
SKIP_DMG=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app)
      APP_DIR="$2"
      shift 2
      ;;
    --skip-dmg)
      SKIP_DMG=1
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: scripts/macos/package-codex-probe-bar.sh [--app path] [--skip-dmg]" >&2
      exit 2
      ;;
  esac
done

if [[ ! -d "$APP_DIR" ]]; then
  "$ROOT/scripts/macos/build-codex-probe-bar.sh"
fi

install -d "$DIST_DIR"
ditto -c -k --keepParent "$APP_DIR" "$ZIP_PATH"
echo "Created: $ZIP_PATH"

if [[ "$SKIP_DMG" -eq 1 ]]; then
  exit 0
fi

if ! command -v hdiutil >/dev/null 2>&1; then
  echo "hdiutil not found; skipped DMG." >&2
  exit 0
fi

STAGING="$(mktemp -d "${TMPDIR:-/tmp}/codex-probe-dmg.XXXXXX")"
ditto "$APP_DIR" "$STAGING/CodexProbeBar.app"
hdiutil create \
  -volname "Codex Probe Bar" \
  -srcfolder "$STAGING" \
  -ov \
  -format UDZO \
  "$DMG_PATH"

echo "Created: $DMG_PATH"
