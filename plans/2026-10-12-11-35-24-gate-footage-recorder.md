# Title: Plan — Gate footage recorder tool

- Classification: feature
- Description: A new CLI tool reads the camera with `LatestFrameReader` and writes 10-minute mp4 parts at a fixed fps. It stops when the disk is low.

---

## Approach Summary / Goal

- `tools/record.py` starts a `LatestFrameReader` and writes frames to `cv2.VideoWriter` (`mp4v`) at a fixed `--fps` (default 15). When no new frame has come, it writes the last frame again, so video time stays the same as real time.
- It starts a new part every 10 minutes, and also when the camera comes back after a drop. When the camera drops, it closes the current part.
- File naming and the disk check are small pure functions, so tests can check them without a camera.
- Goal: record real gate footage for threshold tuning with `eval_offline video`.

## Functional Requirements

- Run with `python -m modules.face_edge.tools.record`.
- Flags:
  - `--config`
  - `--source` (overrides `camera.source`; digits mean a webcam index, same as `cli.py`)
  - `--fps` (default 15)
  - `--part-min` (default 10)
  - `-v`
- Output path: `<data_dir>/recordings/<YYYY-MM-DD>/<HH-MM-SS>.mp4`, using local time when the part starts. With the default config, this is `modules/face_edge/data/recordings/...`.
- Disk check:
  - It checks before each new part and about every 10 s while recording.
  - If free disk < `min_free_gb`, it closes the current file, logs a warning, and exits with code 1.
- Camera drop: it closes the part. Footage starts again in a new file after `LatestFrameReader` reconnects. Reconnect and backoff come from the existing reader and are not changed.
- If the source is a video file, the tool stops when the file ends.
- Ctrl+C closes the current file cleanly and exits with code 0.
- Logs show the RTSP URL through `redact_source()` only.
- `README.md` gets a "Record gate footage" section with the command and the flags.

## Non-Functional Requirements

- Follow `CODING_CONVENTIONS.md`: docstring with usage at the top of the file, full import paths, type hints, and `setup_logging` from `src/cli.py`.
- No new libraries.
- Tests use `tmp_path` and monkeypatch only. No camera, no real `data/` folder.

## Files in Scope

- `modules/face_edge/tools/record.py` (new)
- `modules/face_edge/src/sinks.py`: rename `_free_gb` to `free_gb`, update its one caller (`SnapshotSink.emit`), and add it to `__all__`
- `modules/face_edge/README.md`: new section after "Evaluate offline"; add `record.py` to the `tools/` line in Layout
- `modules/face_edge/tests/test_record.py` (new)

## Risks & Assumptions

- **Assumption:** the time in the file name is `HH-MM-SS`, not `HH:MM:SS`, because colons break on Windows and in some tools.
- **Assumption:** the codec is `mp4v`, because `opencv-python-headless` usually has no H.264. The files are bigger, but `eval_offline` reads them fine.
- **Risk:** recordings are biometric data. They go under `data/`, which the rules already say is never committed. Nothing deletes them automatically, as you chose.
- **Risk:** a 15 fps sub-stream at 640x360 in `mp4v` is about 100–300 MB per 10 minutes. This is a rough estimate that I have not measured.
- `cleanup_old_data()` is not changed.

## Open Questions / Blockers

- None.

## Status

- [x] Ready to execute
- [ ] Blocked

## Task List

| #   | Status | Task | Responsible Role | Dependencies | Acceptance Criteria | Skills |
| --- | ------ | ---- | ---------------- | ------------ | ------------------- | ------ |
| 1   | TODO   | In `src/sinks.py`, rename `_free_gb` to `free_gb`, update `SnapshotSink.emit`, and add it to `__all__` | developer | none | No `_free_gb` is left in the code. The existing tests still pass. | `clean-code` |
| 2   | TODO   | Create `tools/record.py`. Add `part_path(root, start: datetime) -> Path` and `disk_ok(path, min_free_gb) -> bool` (uses `free_gb`). Add a `Recorder` loop with fixed fps, part rotation, closing the part on a drop, the disk stop, the file-end stop, and Ctrl+C handling. Add `main(argv)` with argparse. | developer | 1 | `python -m modules.face_edge.tools.record -h` works. Running it with a short video file as `--source` writes mp4 parts in the right folder. | `clean-code` |
| 3   | TODO   | Add the README section and the Layout line | developer | 2 | The command and flags in the README match `-h`. | — |
| 4   | TODO   | Write `tests/test_record.py`. Check that `part_path` gives the date folder and `HH-MM-SS.mp4`, including midnight and zero-padding. Check that `disk_ok` is True/False above, below, and at the limit (monkeypatch `free_gb`). Check that the recorder stops with exit code 1 and closes the writer when the disk is low (fake reader and fake writer). | tester | 2 | `python -m pytest -q` passes, and the new tests need no camera. | `aaa-testing` |
