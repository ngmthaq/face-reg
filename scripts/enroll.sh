#!/usr/bin/env bash
# Enrolls, lists or removes people in the gallery.
# Usage: bash scripts/enroll.sh --list
set -euo pipefail
cd "$(dirname "$0")/.."      # project root
PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python
exec "$PY" -m face_reg enroll "$@"
