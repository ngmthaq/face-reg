# Title: Plan — Mirror the `--show` preview for webcams

- Classification: bug (missing option)
- Description: Webcam previews look left-right reversed; add a preview-only mirror that is on by default for webcam sources.

---

## Root Cause

Webcams deliver the true (non-mirrored) image. `Preview.show()` (`face_reg/src/tools/overlay.py`) shows it unchanged, so it looks reversed next to video-call apps, which mirror your own image. The pipeline itself is correct.

## Approach

- `face_reg/src/tools/overlay.py`: `draw_overlay(..., mirror=False)` — when on, flip the frame left-right first (`cv2.flip(frame, 1)`), then draw each box at the mirrored x (`x' = width − x − w`) so text is not backwards. `Preview(..., mirror=False)` passes it through.
- `face_reg/src/cli/pipeline_wrapper.py`: `--mirror` / `--no-mirror` on `run` (default: auto). Helper `should_mirror(source, flag) -> bool`: returns `flag` if set, else `True` only for a webcam index (`int` source).
- `face_reg/src/cli/pipeline.py`: `Pipeline.run(show, window, mirror=False)` passes it to `Preview`.
- Not changed: detection/recognition frames, snapshots, events, recordings, `eval_offline`.
- Docs: one line in the root `README.md` Run section.

## Status

- [x] Ready to execute

## Task List

| # | Status | Task | Responsible Role | Dependencies | Acceptance Criteria | Skills |
|---|---|---|---|---|---|---|
| 1 | DONE | Changes above | developer | none | `run -h` shows `--mirror/--no-mirror`; `draw_overlay` with `mirror=False` is pixel-identical to today; no other output changes | `clean-code` |
| 2 | DONE | Regression tests: mirror flips image and box (`x=10,w=50` → `width−60`); `mirror=False` unchanged; `should_mirror`: `0`→True, `"rtsp://…"`→False, file path→False, flag wins | tester | 1 | New tests pass; full suite 0 failures | `aaa-testing` |
