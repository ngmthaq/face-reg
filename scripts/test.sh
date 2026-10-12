#!/usr/bin/env bash
# Runs the module tests.
# Usage: bash scripts/test.sh -q
set -euo pipefail
cd "$(dirname "$0")/.."      # project root
PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python
exec "$PY" -m pytest face_reg/tests "$@"
