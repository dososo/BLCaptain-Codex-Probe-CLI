#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_DIR="$ROOT/build/CodexProbeBar.app"
REQUIRE_SIGNED=0
REQUIRE_NOTARIZED=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app)
      APP_DIR="$2"
      shift 2
      ;;
    --require-signed)
      REQUIRE_SIGNED=1
      shift
      ;;
    --require-notarized)
      REQUIRE_NOTARIZED=1
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: scripts/macos/preflight-codex-probe-bar.sh [--app path] [--require-signed] [--require-notarized]" >&2
      exit 2
      ;;
  esac
done

failures=0

pass() { echo "PASS $1"; }
warn() { echo "WARN $1"; }
fail() { echo "FAIL $1"; failures=$((failures + 1)); }

INFO="$APP_DIR/Contents/Info.plist"
EXECUTABLE="$APP_DIR/Contents/MacOS/CodexProbeBar"
SOURCE_DIR="$ROOT/desktop/macos/CodexProbeBar/Sources"

[[ -d "$APP_DIR" ]] && pass "App bundle exists: $APP_DIR" || fail "App bundle missing: $APP_DIR"
[[ -f "$INFO" ]] && pass "Info.plist exists" || fail "Info.plist missing"
[[ -x "$EXECUTABLE" ]] && pass "Executable exists" || fail "Executable missing or not executable"

if [[ -f "$INFO" ]]; then
  bundle_id="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$INFO" 2>/dev/null || true)"
  lsui="$(/usr/libexec/PlistBuddy -c 'Print :LSUIElement' "$INFO" 2>/dev/null || true)"
  version="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$INFO" 2>/dev/null || true)"
  [[ "$bundle_id" == "com.blcaptain.codexprobe.bar" ]] && pass "Bundle identifier is stable" || fail "Unexpected bundle id: ${bundle_id:-missing}"
  [[ "$lsui" == "true" ]] && pass "LSUIElement menu-bar mode is enabled" || fail "LSUIElement is not true"
  [[ "$version" == "0.9.0" ]] && pass "Bundle version is $version" || fail "Unexpected bundle version: ${version:-missing}"
fi

if grep -R -n -E 'Keychain|SecItemCopyMatching|HTTPCookie|URLSession|WKWebView|SFAuthorization|NEPacketTunnel|CGEventTapCreate' "$SOURCE_DIR" >/tmp/codex-probe-forbidden-api.txt 2>/dev/null; then
  fail "Forbidden privacy/network/system APIs found in macOS source"
  sed -n '1,40p' /tmp/codex-probe-forbidden-api.txt
else
  pass "No forbidden privacy/network/system APIs found in macOS source"
fi

if codesign --verify --deep --strict --verbose=2 "$APP_DIR" >/tmp/codex-probe-codesign.txt 2>&1; then
  pass "Code signature verifies"
  codesign -dv "$APP_DIR" 2>&1 | sed -n '1,20p'
else
  if [[ "$REQUIRE_SIGNED" -eq 1 ]]; then
    fail "Code signature verification failed"
  else
    warn "Code signature verification failed; local beta build is unsigned"
  fi
  sed -n '1,40p' /tmp/codex-probe-codesign.txt
fi

if command -v spctl >/dev/null 2>&1; then
  if spctl --assess --type execute --verbose=4 "$APP_DIR" >/tmp/codex-probe-spctl.txt 2>&1; then
    pass "Gatekeeper assessment passes"
  else
    if [[ "$REQUIRE_SIGNED" -eq 1 ]]; then
      fail "Gatekeeper assessment failed"
    else
      warn "Gatekeeper assessment failed; ordinary downloaded installs may show a warning"
    fi
    sed -n '1,40p' /tmp/codex-probe-spctl.txt
  fi
fi

if command -v xcrun >/dev/null 2>&1; then
  if xcrun stapler validate "$APP_DIR" >/tmp/codex-probe-stapler.txt 2>&1; then
    pass "Notarization staple validates"
  else
    if [[ "$REQUIRE_NOTARIZED" -eq 1 ]]; then
      fail "Notarization staple validation failed"
    else
      warn "Notarization staple validation failed; formal public distribution is not complete"
    fi
    sed -n '1,40p' /tmp/codex-probe-stapler.txt
  fi
fi

if [[ "$failures" -gt 0 ]]; then
  echo "Preflight failed with $failures issue(s)." >&2
  exit 1
fi

echo "Preflight completed."
