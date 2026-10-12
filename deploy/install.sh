#!/usr/bin/env bash
# Installs the face_reg package on a Linux edge device (x86 mini PC, Jetson, Raspberry Pi 5)
# under /opt/face_reg. Run from anywhere:  sudo bash deploy/install.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"     # project root
DST=/opt/face_reg

id face_reg >/dev/null 2>&1 || useradd --system --home "$DST" --shell /usr/sbin/nologin face_reg
mkdir -p "$DST"
# code + models; never overwrite data or an already-edited config on reinstall
rsync -a --exclude .venv --exclude /data --exclude /photos --exclude '__pycache__' --exclude .git --exclude .claude --exclude graphify-out --exclude .pytest_cache --exclude /config.yaml \
      "$ROOT"/ "$DST"/
[ -f "$DST/config.yaml" ] || cp "$ROOT/config.yaml" "$DST/config.yaml"
mkdir -p "$DST/data/gallery"

python3 -m venv "$DST/.venv"
"$DST/.venv/bin/pip" install -q --upgrade pip
"$DST/.venv/bin/pip" install -q -r "$DST/requirements.txt"
# Jetson: replace onnxruntime with NVIDIA's onnxruntime-gpu wheel for your JetPack.
# Intel:  pip install onnxruntime-openvino  and set providers: [OpenVINOExecutionProvider]

bash "$DST/scripts/download_models.sh"

chown -R face_reg:face_reg "$DST"
chown root:face_reg "$DST/config.yaml"
chmod 640 "$DST/config.yaml"
chmod -R go-rwx "$DST/data"
cp "$DST/deploy/face_reg.service" /etc/systemd/system/face_reg.service
systemctl daemon-reload
echo
echo "Installed. Next:"
echo "  1. edit $DST/config.yaml (camera.source, device_id)"
echo "  2. enroll: cd $DST && sudo -u face_reg .venv/bin/python -m face_reg enroll --person-id emp_0001   # photos in $DST/photos/emp_0001/"
echo "  3. sudo systemctl enable --now face_reg && journalctl -u face_reg -f"
