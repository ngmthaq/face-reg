# Title: Plan — Round 3: code quality refactor

- Classification: feature (refactor)
- Description: Lock in today's behaviour with tests, then split the big functions, add an `Event` type, and fix the small clean-code findings. Outputs do not change.

---

## Approach Summary / Goal

- **Tests first:** the tester writes characterization tests that record today's outputs. These are JSONL lines, `enroll` stdout, gallery files and sink order. They use a fake detector, liveness model and recognizer, so they run with no model files. They must pass before and after the refactor.
- **Two developers in parallel on separate files:** one does groups A + C (pipeline, sinks, event type). The other does group B (enroll, cli). Then a third developer does group D (small fixes in every file).
- **Then the tester** updates the old tests for the new `Event` type and runs everything.
- Goal: the clean-code findings are closed, and outputs stay byte-for-byte the same.

## Functional Requirements

1. JSONL event lines, `undecided.json`, `enroll` stdout and stderr, `--list` output, and gallery files are exactly the same as before. The characterization tests prove this.
2. **A:** `Pipeline.process` is at most about 25 lines, at most 2 levels of nesting, and calls helpers (`_handle_lost_tracks`, `_evaluate_face`, `_decide`, `_in_cooldown`, `_emit`). `Pipeline.run` uses `_housekeeping(now, reader)` and a `Preview` class in `overlay.py`, so `pipeline.py` no longer calls `cv2.namedWindow`, `imshow` or `waitKey`. `_log_undecided` becomes the public `flush_undecided`, and `eval_offline` uses it. `stream._redact` becomes the public `redact_source`, imported at the top of the file. The wrapper in `pipeline.py` is deleted.
3. **C:** `datatypes.py` gets an `Event` dataclass with `to_dict()`. `to_dict()` gives the same keys in the same order as today's dict. Sinks take an `Event`. `SnapshotSink` sets `event.snapshot`. `JsonlSink` writes `event.to_dict()`. `build_sinks` uses a `SINK_FACTORIES` dict. The `snapshot` → `jsonl` → `console` → `relay` order stays.
4. **B:** `enroll.main` sends work to `_cmd_list`, `_cmd_remove`, `_cmd_batch` and `_cmd_enroll`. `Enroller.enroll` makes no `print` calls. It returns an `EnrollResult` (count plus output lines), and `main` prints the lines. `enroll.main` does not call `logging.basicConfig`. `cli.main` calls `setup_logging(level=WARNING)` before it hands off to `enroll`. `log` is moved up with the constants. Imports are sorted.
5. **D:**
   - `recognize.py`: add an `_atomic_write(path, writer)` helper that both `Gallery` save paths use.
   - Named constants: `CLEANUP_EVERY_S=3600`, `EMBED_DIM=128`, JPEG quality values, snapshot crop pad, ONNX thread count, and the eval latency values.
   - No `;` that joins two statements.
   - `eval_offline.eval_video` split into `_replay`, `_write_overlay` and `_print_summary`.
   - Type hints on `_make_event(face)` and the liveness `bbox`.

## Non-Functional Requirements

- No new dependencies. Full-path imports. Follow CODING_CONVENTIONS.
- Speed per frame stays the same (no new copies of frames or arrays).

## Files in Scope

- `modules/face_edge/src/pipeline.py`, `overlay.py`, `datatypes.py`, `sinks.py`, `enroll.py`, `cli.py`
- `modules/face_edge/src/stages/stream.py`, `recognize.py`, `liveness.py`
- `modules/face_edge/tools/eval_offline.py`
- `modules/face_edge/tests/test_characterization.py` (new), `test_core.py`, `test_security.py`, `test_models.py` (updates for `Event`)

## Risks & Assumptions

- Risk: this is the largest round. It changes most files in `src/`. The characterization tests are the safety net. If one fails after the refactor, the refactor is wrong, not the test.
- Risk: the `--show` preview window cannot be tested automatically (it needs a display). I will check `Preview` by reading the code. You may want to try `run --show` by hand once.
- Assumption: no outside code reads `Pipeline.events` as dicts. Only `eval_offline` does, and it is updated.
- Assumption: when `enroll` is started through `cli.py`, its logging stays at `WARNING`.

## Open Questions / Blockers

- None.

## Status

- [x] Ready to execute
- [ ] Blocked — requires user input on: —

## Task List

| # | Status | Task | Responsible Role | Dependencies | Acceptance Criteria | Skills |
|---|---|---|---|---|---|---|
| 0 | DONE | New `tests/test_characterization.py`. Use a fake detector, liveness model and recognizer (monkeypatched into `pipeline`) and fixed timestamps. Record the exact JSONL lines for: RECOGNIZED after 3 votes; SPOOF_SUSPECTED; cooldown suppression; UNDECIDED timeout and track_lost (via `undecided` content); a sink that raises does not stop the next sink. Also record `enroll` stdout with a faked `check_photo` (accepted, rejected, no front, missing angles), `--list` and `--remove` stdout, the `build_sinks` order, and the gallery file round-trip with mode 0600. Check only outputs, not return types. | tester | none | All tests pass on today's code; no real photos, data or models are used | `aaa-testing` |
| 1 | DONE | Group A + C: FR 2 and FR 3 in `pipeline.py`, `overlay.py`, `stream.py`, `datatypes.py`, `sinks.py`, `tools/eval_offline.py` | developer | 0 | `test_characterization.py` passes with no changes; `--help` commands run; no cv2 window calls in `pipeline.py` | `clean-code` |
| 2 | DONE | Group B: FR 4 in `enroll.py` and `cli.py` | developer | 0 (runs at the same time as 1) | `test_characterization.py` enroll tests pass with no changes; no `print` in `Enroller`; no `basicConfig` in `enroll.py` | `clean-code` |
| 3 | DONE | Group D: FR 5 in `recognize.py`, `sinks.py`, `pipeline.py`, `liveness.py`, `eval_offline.py` | developer | 1, 2 | Characterization tests still pass; `grep` finds no `;`-joined statements in `src/` and `tools/`; constants are named | `clean-code` |
| 4 | DONE | Update `test_core.py`, `test_security.py` and `test_models.py` where they pass dicts to sinks or read `pipe.events` as dicts. Run the full suite. | tester | 3 | Full suite passes; `test_characterization.py` is not changed after task 0 | `aaa-testing` |

## Review Note

- Task 2 first run was blocked: the `--batch` fake in `test_security.py` returned an int. Answered from task 4 (test helpers are updated for new types); the tester changed the fake to return `EnrollResult(0, [])`.
- `test_characterization.py` was not edited after task 0 (last change 11:17, before any source change). It passes on the new code.
- Extra check: `eval_offline video` smoke run on a blank video with a temp config, with and without `--out`: exit 0.
- Review decision: accepted. 55 passed, 1 skipped. Secrets scan: no secrets.
- Low recommendations: `enroll` now prints photo rows after all photos are checked (same text and order); `_atomic_write` leaves the temp file if the writer raises; the `--show` preview was checked by reading only.
