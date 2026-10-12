#!/usr/bin/env bash
# Evaluates thresholds on photos or videos.
# Usage: bash scripts/eval.sh photos --dir test_photos/
set -euo pipefail
cd "$(dirname "$0")/.."      # project root
PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python
exec "$PY" -m face_reg.src.tools.eval_offline "$@"
