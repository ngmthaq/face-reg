# AIE — face_reg

Offline face recognition with liveness for one gate camera on an edge device. This is the only
README in the project.

```
camera stream → face detection → quality check → liveness → recognition → decision → sinks
   (thread)       YuNet            size/blur/yaw    MiniFASNet   SFace + NumPy    5-frame vote   jsonl / snapshot / console / relay
```

One Python app on the edge device: it reads one camera, recognizes enrolled people, rejects
photo/screen attacks, and writes one event per person to a local log (plus an optional door relay).
No database, no API, no server.

There are no `__init__.py` files: `face_reg/` and its sub-folders are namespace packages (Python 3.3+),
so import with full paths (`from face_reg.stages.step_2_detect import YuNetDetector`) and run
everything from the project root.

## Quick start (laptop, macOS / Linux, Python 3.10+)

```bash
cd face-reg                          # the project root; run every command from here
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash scripts/download_models.sh      # YuNet + SFace (~39 MB) into models/; liveness models are already there
```

### Enrollment photos

Put your photos in `photos/<employee_id>/<angle>.jpg`. The folder name is the employee ID, and the
file name is the angle:

```
photos/
├── emp_0001/
│   ├── front.jpg     required: look straight at the camera
│   ├── left.jpg      head turned ~15–25° to the person's left
│   ├── right.jpg     head turned ~15–25° to the person's right
│   ├── up.jpg        chin slightly up
│   └── down.jpg      chin slightly down
└── emp_0002/
    └── ...
```

- `front` is required; the other angles are optional but improve recognition at the gate.
- More than one photo per angle: number them, e.g. `front_2.jpg`, `left-2.jpg`.
- Any other file name is rejected (`BAD_FILE_NAME`). Allowed extensions: jpg, jpeg, png, bmp, webp.
- Keep each turn under 30°; wider turns are rejected (`POSE_TOO_WIDE`).
- Use good light, one face per photo, and no sunglasses or mask.

There is no enroll command. While `run` is running, it scans `photos/` and keeps the gallery in sync
with the folders. The first scan runs at start, then one every `enroll.scan_interval_s` seconds
(default 300, set in `config.yaml`; `enroll.photos_dir` and `enroll.skip_liveness` are in the same block).
The running pipeline picks up the new gallery within 5 s after a scan.

- A new or changed folder is enrolled again (this **replaces** that person's vectors). Results are in the log.
- A folder that did not change is not checked again. A rejected folder is retried only after you change it.
  If the `front` photo is rejected, the person's old vectors stay.
- **Deleting a folder removes that person.** If `photos/` is empty or missing, everyone is removed
  (the log shows a warning). Keep the photos on the device.
- Folder names must be 1-64 characters of letters, digits, `_` or `-`; other folders are skipped with a warning.
- There are no names: the folder name is the person id.

These are biometric data: everything in `photos/` except `.gitkeep` is git-ignored.

### Run

Run on the webcam (`camera.source: 0`) with a preview window:

```bash
python -m face_reg run --show                       # window fits in 1280x720 by default
python -m face_reg run --no-show                    # force the window off (overrides display.show: true)
python -m face_reg run --show --window 960x540        # smaller window
python -m face_reg run --show --no-mirror            # webcam preview is mirrored by default
python -m face_reg run --source "rtsp://USER:PASSWORD@CAMERA_IP:554/Streaming/Channels/102"
python -m face_reg run --source recording.mp4
```

The `--show` preview is mirrored for webcams, like a video call; use `--no-mirror` / `--mirror` to override.
Detection and saved images are never mirrored.

`--show` / `--no-show` and `--window WxH` override the `display:` block in `config.yaml`
(`display.show`, default `false`; `display.window`, default `1280x720`). Without a flag the config value is used.
If you had an older `.venv` with the headless build, run `pip uninstall opencv-python-headless`
and then `pip install --force-reinstall opencv-python` once.

On macOS the first webcam run asks for camera permission for your terminal app.
Events go to `data/events/<date>.jsonl`, snapshots to `data/snapshots/<date>/`, the gallery to
`data/gallery/`. All paths are set in `config.yaml` and resolve against the project root.

Helper scripts in `scripts/` run the same commands from any folder and use `.venv` when it exists:
`run.sh`. Example: `bash scripts/run.sh --show`.

## Event (one JSON line per decision)

```json
{
  "event_id": "gate-1-20261012-000001",
  "type": "RECOGNIZED",
  "device_id": "gate-1",
  "track_id": 1,
  "occurred_at": "2026-10-12T09:52:14.381+07:00",
  "person_id": "emp_0001",
  "person_name": "Nguyen Van A",
  "scores": {
    "similarity": 0.61,
    "second_best": 0.38,
    "live": 0.96,
    "frames_voted": 4
  },
  "bbox": [124.6, 110.6, 169.1, 250.7],
  "snapshot": "snapshots/2026-10-12/gate-1-20261012-000001.jpg",
  "model": {
    "detector": "yunet_2023mar",
    "liveness": "minifasnet_v2_2.7_80x80+minifasnet_v1se_4.0_80x80",
    "recognizer": "sface_2021dec"
  }
}
```

`type` is `RECOGNIZED`, `UNKNOWN` or `SPOOF_SUSPECTED` (`person_id` is null for the last two).
`UNDECIDED` tracks are only logged (with best scores, for tuning), never emitted.

## Decision rules (over the last 5 frames that passed quality)

| Decision        | Rule                                                                        |
| --------------- | --------------------------------------------------------------------------- |
| RECOGNIZED      | ≥ 3 live frames, same top-1 person, similarity ≥ 0.45, top-1 − top-2 ≥ 0.05 |
| SPOOF_SUSPECTED | ≥ 3 frames with live < 0.8 — **spoof wins ties**                            |
| UNKNOWN         | 5 live frames, nobody reaches the recognized rule                           |
| UNDECIDED       | track lost, or no decision 3 s after its first good frame → log only        |

One event per track; the same `person_id` is not re-emitted for 10 s (cooldown).
All thresholds are in `config.yaml` and are **starting values** — tune them on real gate footage.

## Deploy on the edge device (Linux)

```bash
sudo bash scripts/deploy/install.sh                     # -> /opt/face_reg, apt libs, venv, models, systemd unit
sudo nano /opt/face_reg/config.yaml            # camera.source (sub-stream!), device_id
sudo systemctl enable --now face_reg
journalctl -u face_reg -f                      # EVENT lines + HEARTBEAT every 60 s (fps, faces, camera state, ms/stage)
```

### Monitor on the edge device

To see the live preview on a monitor plugged into the device:

1. Use a desktop with auto-login on display `:0` (X11, or Wayland with XWayland).
2. Set `display.show: true` in `/opt/face_reg/config.yaml`.
3. Run `sudo systemctl restart face_reg`.

The installer adds an autostart entry that runs `xhost +SI:localuser:face_reg`, so only the `face_reg`
user may draw on the desktop. It takes effect at the next desktop login. If no display can be reached,
the app logs a warning, keeps recognizing, and tries again every 30 s. Pressing q or Esc in the window stops the app
(systemd restarts it after 3 s).

On the device: code in `/opt/face_reg`, data in `/opt/face_reg/data`, config in
`/opt/face_reg/config.yaml`, service and user `face_reg`. The installer does not copy
`photos/` or `data/`, and it keeps an already-edited `config.yaml` on reinstall.

- **Speed**: use the camera sub-stream (640×360/720p), not 4K. If fps falls short: lower `process_fps` to 3,
  use `onnxruntime-openvino` (Intel) or NVIDIA's onnxruntime-gpu (Jetson) and set `models.providers`.
- **Door output**: add `relay` to `sinks` and set `relay.mode` to `gpio` (Pi/Jetson, `pip install gpiozero`)
  or `command` (any USB relay CLI). `mode: log` is a dry run.
  In `command` mode, `relay.command` and `relay.off_command` are argument lists (for example
  `[usbrelay, HURTM_1=1]`), run without a shell. The off command runs after `pulse_s`.
- **Gallery update**: add, change or delete a folder in `photos/` on the device. The running service scans it every `enroll.scan_interval_s` seconds and reloads the gallery within 5 s, no restart needed.

## Layout

```
face-reg/                          project root: run every command from here
├── face_reg/                      code only
│   ├── __main__.py                entry point: python -m face_reg run
│   ├── main.py                    CLI dispatcher: run
│   ├── entry/                     files in call order from main.py:
│   │                              step_1_pipeline_wrapper.py (the run command)
│   │                              step_2_pipeline.py (wires the stages, cooldown, timeout, heartbeat, retention cleanup)
│   │                              step_3_photo_scanner.py (background thread: syncs the gallery with photos/)
│   │                              step_4_enroll.py (gallery logic: same detect/quality/liveness checks as the stream; audit log)
│   ├── configs/                   config.yaml -> pydantic; one class per file, config.py loads it
│   ├── datatypes/                 Face, Track, FrameResult, Decision, ... (one class per file)
│   ├── stages/                    step_1_stream, step_2_detect, step_3_tracker, step_4_quality,
│   │                              step_5_liveness, step_6_recognize, step_7_decide
│   └── tools/                     logs.py, sinks.py, overlay.py, export_liveness_onnx.py
├── config.yaml                    settings (every threshold, camera, relay)
├── data/                          gallery, events, snapshots (git-ignored, biometric)
├── photos/                        enrollment photos, photos/<employee_id>/<angle>.jpg (git-ignored except .gitkeep)
├── scripts/                       shell helpers: download_models, run
│   └── deploy/                    install.sh, face_reg.service (systemd, Restart=always), face_reg-xhost.desktop
├── models/                        ONNX models
├── plans/                         plan files
├── README.md                      the only README
├── requirements.txt
└── .gitignore
```

## Models and licenses

| Stage       | Model                                                                                             | License    |
| ----------- | ------------------------------------------------------------------------------------------------- | ---------- |
| Detection   | YuNet 2023mar (OpenCV zoo)                                                                        | MIT        |
| Recognition | SFace 2021dec (OpenCV zoo)                                                                        | Apache 2.0 |
| Liveness    | Silent-Face-Anti-Spoofing MiniFASNetV2 (scale 2.7) + MiniFASNetV1SE (scale 4.0), exported to ONNX | Apache 2.0 |

Re-check each repo and model card before commercial delivery. The liveness ONNX files were exported with
`face_reg/tools/export_liveness_onnx.py` (max difference vs. PyTorch ≈ 1e-6); preprocessing matches the original repo
(BGR, 0–255, crop scale per model, softmax class 1 = real, models averaged).

RGB-only liveness stops printed photos and phone/tablet screens; it is weak against high-quality masks or
replays on large screens.

## Biometric data

The gallery and snapshots are biometric data. `data/` is git-ignored, files are written
`0600`, and the systemd unit sets `UMask=0077`. Enable disk encryption where the device supports it, restrict
access to `photos/` (the app needs the photos to keep the gallery in sync; the deploy
script does not copy this folder to the device), and collect consent at enrollment.
`data/gallery/audit.jsonl` records who was enrolled/removed by the scan. Snapshots and logs older than `retention_days`
(30) are deleted automatically; snapshots stop when free disk < `min_free_gb`.
