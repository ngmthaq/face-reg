# Title: Plan — Hot reload of the gallery

- Classification: feature
- Description: The live loop checks the gallery files every 5 s and swaps in a new `Gallery` when they change.

---

## Approach Summary / Goal

- Add a gallery check to `Pipeline._housekeeping()` in `src/pipeline.py`. It runs every 5 s, like the cleanup and heartbeat jobs.
- The check reads the mtime (last change time) of `gallery.npz` and `persons.json`. If either one changed since the last load, it loads a new `Gallery` and swaps it in with one assignment (`self.gallery = new`).
- If the load fails (broken file, missing `gallery.npz`), the old gallery stays and an error is logged.
- Goal: a new enrollment works without restarting the service.

## Functional Requirements

- FR1: Every 5 s (`GALLERY_CHECK_S = 5`), the live loop compares the mtimes of `gallery.npz` and `persons.json` with the values seen at the last good load.
- FR2: When either mtime changed, the pipeline loads a new `Gallery` and replaces `self.gallery`.
- FR3: After a good reload, it logs at INFO: `gallery reloaded: N vectors / M people`.
- FR4: When the load raises an error (bad npz, bad JSON), the old gallery stays and an ERROR log is written with the reason. The service does not crash.
- FR5: When `gallery.npz` is missing, the old gallery stays and an ERROR log is written.
- FR6: After a failed load, the pipeline does not log the same error every 5 s for the same broken file. It tries again only when an mtime changes again.
- FR7: Tracks that are open at reload time are not changed.
- FR8: The enroll output no longer says to restart. New text: `   the running service loads the new gallery within 5 seconds`. The docstring in `src/enroll.py` and `README.md:116` say the same.

## Non-Functional Requirements

- The check costs only two `stat` calls every 5 s. No extra thread.
- The swap is one attribute assignment, so `process()` never sees a half-built gallery.
- Code works on Python 3.10.

## Files in Scope

- `modules/face_edge/src/pipeline.py` — change
- `modules/face_edge/src/enroll.py` — change (docstring, output line)
- `modules/face_edge/README.md` — change (line 116)
- `modules/face_edge/tests/test_characterization.py` — change (enroll output test, if it checks the old text)
- `modules/face_edge/tests/test_gallery_reload.py` — new

## Risks & Assumptions

- `Gallery.save()` writes two files one after the other. A reload can happen between the two writes. The next check (5 s later) sees the new `persons.json` mtime and loads again. So names can be wrong for at most about 5 s.
- Some file systems have a coarse mtime (1–2 s). Two saves within that time can look like one change. This is fine for a gate device.
- A person removed from the gallery can still be decided by an open track for a few seconds (user choice: leave tracks).
- The check runs only in `run()` (live loop). `tools/eval_offline.py` does not reload. That is fine.

## Open Questions / Blockers

- None.

## Status

- [x] Ready to execute
- [ ] Blocked

## Task List

| #   | Status | Task | Responsible Role | Dependencies | Acceptance Criteria | Skills |
| --- | ------ | ---- | ---------------- | ------------ | ------------------- | ------ |
| 1 | DONE | In `src/pipeline.py`: add `GALLERY_CHECK_S = 5`; save the mtimes of both gallery files after the first load in `__init__`; add a method `reload_gallery_if_changed()` (public, so tests can call it); call it from `_housekeeping()` every `GALLERY_CHECK_S` seconds. | developer | none | FR1–FR7 are met. Good reload logs `gallery reloaded: N vectors / M people`. Broken or missing file keeps the old gallery and logs ERROR once per change. Existing tests still pass. | `clean-code` |
| 2 | DONE | In `src/enroll.py`: change the docstring line and the output line at line 221 to the new text (FR8). In `README.md:116`: say the service picks up the new gallery within 5 s, no restart needed. | developer | none | No "restart" text about the gallery is left in `enroll.py` or the README gallery-update line. | `clean-code` |
| 3 | DONE | Add `tests/test_gallery_reload.py` with a pipeline built like `make_pipe`. Tests: (a) save a new gallery → reload → `pipe.gallery` has the new vectors and the INFO log text is right; (b) write a broken `gallery.npz` → old gallery kept, ERROR logged; (c) delete `gallery.npz` → old gallery kept, ERROR logged; (d) no change → no reload. Update the enroll output test in `test_characterization.py` if it checks the old text. | tester | tasks 1, 2 | All new tests pass. Full suite `python -m pytest -q` passes. Tests follow AAA. | `aaa-testing` |
