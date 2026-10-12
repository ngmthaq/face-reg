#!/usr/bin/env bash
# Runs the face recognition app.
# Usage: bash scripts/run.sh --show
set -euo pipefail
cd "$(dirname "$0")/.."      # project root
PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python
exec "$PY" -m face_reg run "$@"
