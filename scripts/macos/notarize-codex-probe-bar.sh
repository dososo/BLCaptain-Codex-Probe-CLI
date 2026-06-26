#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_DIR="${1:-${CODEX_PROBE_APP_DIR:-$HOME/Applications/CodexProbeBar.app}}"
DIST_DIR="$ROOT/dist"
ARCHIVE="$DIST_DIR/CodexProbeBar-notary.zip"
PASSWORD="${APPLE_APP_SPECIFIC_PASSWORD:-${AC_PASSWORD:-}}"

if [[ ! -d "$APP_DIR" ]]; then
  echo "App bundle not found: $APP_DIR" >&2
  echo "Run build and signing before notarization." >&2
  exit 2
fi

if [[ -z "${APPLE_ID:-}" || -z "${APPLE_TEAM_ID:-}" || -z "$PASSWORD" ]]; then
  echo "Missing Apple notarization credentials." >&2
  echo "Required: APPLE_ID, APPLE_TEAM_ID, and APPLE_APP_SPECIFIC_PASSWORD or AC_PASSWORD." >&2
  exit 2
fi

codesign --verify --deep --strict --verbose=2 "$APP_DIR"
install -d "$DIST_DIR"
ditto -c -k --keepParent "$APP_DIR" "$ARCHIVE"

xcrun notarytool submit "$ARCHIVE" \
  --apple-id "$APPLE_ID" \
  --team-id "$APPLE_TEAM_ID" \
  --password "$PASSWORD" \
  --wait

xcrun stapler staple "$APP_DIR"
xcrun stapler validate "$APP_DIR"
spctl --assess --type execute --verbose=4 "$APP_DIR"

echo "Notarized and stapled: $APP_DIR"
