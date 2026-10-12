#!/usr/bin/env bash
# Records the camera stream to video parts.
# Usage: bash scripts/record.sh --source 0 --fps 15
set -euo pipefail
cd "$(dirname "$0")/.."      # project root
PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python
exec "$PY" -m face_reg.src.tools.record "$@"
