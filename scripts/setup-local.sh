#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT_DIR"

if [[ ! -x ".venv/bin/python" ]]; then
  "$PYTHON_BIN" -m venv .venv
fi

.venv/bin/python -m pip install .

if [[ "$#" -eq 0 ]]; then
  .venv/bin/codex-probe --db .probe/setup-demo.db setup --demo
else
  .venv/bin/codex-probe "$@"
fi
