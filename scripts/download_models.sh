#!/usr/bin/env bash
# Downloads the YuNet detector and SFace recognizer from the OpenCV model zoo into models/.
# The liveness models (minifasnet_*.onnx) are already in models/; to rebuild them see
# face_reg/tools/export_liveness_onnx.py.
# Every model is checked against a pinned SHA-256; a mismatch stops the script.
set -euo pipefail
cd "$(dirname "$0")/.."      # project root
MODELS_DIR="${MODELS_DIR:-models}"
mkdir -p "$MODELS_DIR"
BASE=https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models

YUNET_SHA=8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4
SFACE_SHA=0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79
LIVE_V1SE_SHA=f0beff994c3f3d2c7797fdfbcc746aab61d0b3543dd68d731ba5bcf3e19a1f96
LIVE_V2_SHA=5add8d901d04f8ab4df159f0dbea2cef4fb18909b7f693f74bfc9d2b338b2c73

sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | cut -d' ' -f1
  else
    shasum -a 256 "$1" | cut -d' ' -f1
  fi
}

fetch() {
  local url=$1 out=$2 min_bytes=$3 sha=$4
  if [ -f "$out" ] && [ "$(wc -c < "$out")" -ge "$min_bytes" ]; then
    if [ "$(sha256_of "$out")" != "$sha" ]; then
      echo "ERROR: $out has an unexpected SHA-256 (file kept, check it)" >&2; exit 1
    fi
    echo "ok      $out"; return
  fi
  echo "fetch   $out"
  curl -fL --retry 3 -o "$out.part" "$url"
  if [ "$(wc -c < "$out.part")" -lt "$min_bytes" ]; then
    echo "ERROR: $out looks truncated (git-lfs pointer?)" >&2; rm -f "$out.part"; exit 1
  fi
  if [ "$(sha256_of "$out.part")" != "$sha" ]; then
    echo "ERROR: $out download has an unexpected SHA-256" >&2; rm -f "$out.part"; exit 1
  fi
  mv "$out.part" "$out"
}

check_existing() {
  local f=$1 sha=$2
  if [ ! -f "$f" ]; then
    echo "MISSING $f  -> run face_reg/tools/export_liveness_onnx.py"; return
  fi
  if [ "$(sha256_of "$f")" != "$sha" ]; then
    echo "ERROR: $f has an unexpected SHA-256 (file kept, check it)" >&2; exit 1
  fi
  echo "ok      $f"
}

fetch "$BASE/face_detection_yunet/face_detection_yunet_2023mar.onnx" \
      "$MODELS_DIR/face_detection_yunet_2023mar.onnx" 200000 "$YUNET_SHA"
fetch "$BASE/face_recognition_sface/face_recognition_sface_2021dec.onnx" \
      "$MODELS_DIR/face_recognition_sface_2021dec.onnx" 30000000 "$SFACE_SHA"

check_existing "$MODELS_DIR/minifasnet_v2_2.7_80x80.onnx" "$LIVE_V2_SHA"
check_existing "$MODELS_DIR/minifasnet_v1se_4.0_80x80.onnx" "$LIVE_V1SE_SHA"
