#!/usr/bin/env bash
# Installs the face_reg package on a Linux edge device (x86 mini PC, Jetson, Raspberry Pi 5)
# under /opt/face_reg. Run from anywhere:  sudo bash scripts/deploy/install.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"  # project root
DST=/opt/face_reg

id face_reg >/dev/null 2>&1 || useradd --system --home "$DST" --shell /usr/sbin/nologin face_reg
mkdir -p "$DST"
# code + models; never overwrite data or an already-edited config on reinstall
rsync -a --exclude .venv --exclude /data --exclude /photos --exclude '__pycache__' --exclude .git --exclude .claude --exclude graphify-out --exclude /config.yaml \
      "$ROOT"/ "$DST"/
[ -f "$DST/config.yaml" ] || cp "$ROOT/config.yaml" "$DST/config.yaml"
mkdir -p "$DST/data/gallery"

# system libraries for the opencv-python GUI build and xhost (preview on a monitor)
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -q
  apt-get install -y libgl1 x11-xserver-utils
  apt-get install -y libglib2.0-0t64 || apt-get install -y libglib2.0-0
fi

python3 -m venv "$DST/.venv"
"$DST/.venv/bin/pip" install -q --upgrade pip
# the headless and GUI builds clash in one venv
"$DST/.venv/bin/pip" uninstall -y -q opencv-python-headless || true
"$DST/.venv/bin/pip" install -q -r "$DST/requirements.txt"
# Jetson: replace onnxruntime with NVIDIA's onnxruntime-gpu wheel for your JetPack.
# Intel:  pip install onnxruntime-openvino  and set providers: [OpenVINOExecutionProvider]

bash "$DST/scripts/download_models.sh"

chown -R face_reg:face_reg "$DST"
chown root:face_reg "$DST/config.yaml"
chmod 640 "$DST/config.yaml"
chmod -R go-rwx "$DST/data"
cp "$DST/scripts/deploy/face_reg.service" /etc/systemd/system/face_reg.service
# lets the service user draw on the desktop; takes effect at the next desktop login
mkdir -p /etc/xdg/autostart
cp "$DST/scripts/deploy/face_reg-xhost.desktop" /etc/xdg/autostart/face_reg-xhost.desktop
systemctl daemon-reload
echo
echo "Installed. Next:"
echo "  1. edit $DST/config.yaml (camera.source, device_id)"
echo "  2. enroll: put photos in $DST/photos/<id>/front.jpg (the running service scans photos/ and picks them up)"
echo "  3. optional monitor: set display.show: true in config.yaml (desktop auto-login on :0)"
echo "  4. sudo systemctl enable --now face_reg && journalctl -u face_reg -f"
