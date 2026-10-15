# Plan — Auto-enroll by scanning the photos folder

- Classification: feature
- Description: Remove the manual enroll CLI. A background thread in `run` scans `photos/` every `enroll.scan_interval_s` seconds and keeps the gallery in sync with the folders.

---

## Approach Summary / Goal

- A new `PhotoScanner` class runs in a daemon thread inside `Pipeline.run()`. It uses the existing `Enroller` checks (detect, quality, liveness, duplicate), with its own model instances, so the camera loop never waits.
- Each scan reloads the gallery from disk. It compares each folder's file signature (names, sizes, modified times) with `data/gallery/scan_state.json`. It re-enrolls only new or changed folders, removes people whose folder is gone, and saves the gallery once if anything changed.
- The pipeline already reloads the gallery when its files change (checked every 5 s), so no new reload code is needed.
- Goal: no manual enroll step. You add, change, or delete a folder in `photos/`, and the gallery follows.

## Functional Requirements

- FR1: Add a new `enroll:` config block: `scan_interval_s` (default 300, must be > 0), `photos_dir` (default `photos`, relative to the project root), `skip_liveness` (default false).
- FR2: The first scan runs when `run` starts. After that, a scan runs every `scan_interval_s` seconds.
- FR3: Each sub-folder whose name matches `PERSON_ID_RE` is one person. Folders with a bad name are skipped, with a warning logged once per change.
- FR4: A new folder, or a folder whose files changed since the last scan, is enrolled with `Enroller.enroll(person_id, None, photos)`. The scanner logs the result lines (INFO for accepted, WARNING for rejected).
- FR5: A folder that did not change is not checked again. This includes a folder that was rejected: it is retried only after it changes.
- FR6: A rejected folder (no valid `front.jpg`) keeps that person's old vectors. This is the current `Enroller` behaviour.
- FR7: A person in the gallery with no matching folder is removed (full sync). This also applies when `photos/` is missing or empty: everyone is removed.
- FR8: Every enroll and remove writes an `audit.jsonl` line, with `"source": "scan"`.
- FR9: The gallery is saved (atomic write, already in place) only when something changed. The state file is saved after the gallery.
- FR10: Delete the manual enroll CLI: `scripts/enroll.sh`, `face_reg/src/cli/enroll_wrapper.py`, and the `enroll` sub-command in `main.py`. `PHOTOS_DIR` in `config.py` is replaced by `cfg.enroll.photos_dir`.
- FR11: Names: there is no name source any more. New people have no name. Existing names in `persons.json` stay (`Enroller` keeps the old name when `name` is None).

## Non-Functional Requirements

- The scan thread must never crash `run`. Any error is logged with `log.exception` and the next scan still runs.
- The scan thread stops cleanly when `run` stops (a `threading.Event`, joined in the `finally` block).
- No model objects are shared between the scan thread and the frame loop. OpenCV DNN objects are not thread-safe.
- Follow `.claude/references/CODING_CONVENTIONS.md`. Logger name: `face_reg.enroll`.

## Files in Scope

- **New:** `face_reg/src/configs/enroll_cfg.py` (`EnrollCfg`)
- **New:** `face_reg/src/cli/photo_scanner.py` (`PhotoScanner`: `scan_once()`, `start()`, `stop()`)
- **Change:** `face_reg/src/configs/config.py` (add the `enroll` field, remove `PHOTOS_DIR`)
- **Change:** `face_reg/src/cli/enroll.py` (gallery reload helper if needed, `audit` source field; keep `Enroller`, `expand_photos`)
- **Change:** `face_reg/src/cli/pipeline.py` (start/stop the scanner in `run()`)
- **Change:** `face_reg/src/main.py`, `face_reg/__main__.py` (remove the `enroll` command and docstrings)
- **Change:** `config.yaml` (add the `enroll:` block)
- **Change:** `README.md`, `scripts/deploy/install.sh` (line 45 hint), `.claude/references/PROJECT_OVERVIEW.md`, `.claude/references/CODING_CONVENTIONS.md` (docs)
- **Delete:** `scripts/enroll.sh`, `face_reg/src/cli/enroll_wrapper.py`

## Risks & Assumptions

- **Privacy change:** The README now says "delete photos after enrolling". With full sync, deleting a folder **removes that person**. Photos must stay on the device. The README will say this clearly.
- **Empty folder wipes the gallery:** You chose "remove everyone". If `photos/` is missing or not mounted, the whole gallery is cleared on the next scan. The scanner logs a WARNING when this happens.
- **Half-copied folders:** If you copy photos while a scan runs, the scanner may enroll part of the photos. The next scan sees the change and re-enrolls, so it fixes itself.
- **CPU:** Enrolling uses CPU in the same process. It may lower FPS a little during a scan. It only happens when folders change.
- **No `--list` / `--remove` any more:** You see the gallery through the logs. You remove someone by deleting their folder.
- **Assumption:** The scanner runs only in `run`. Nothing else writes the gallery, so there is no write race.
- **Assumption:** No tests (your choice). I check the work by running the app with `scan_interval_s: 5`.

## Open Questions / Blockers

- None.

## Status

- [x] Ready to execute
- [ ] Blocked

## Task List

| #   | Status | Task | Responsible Role | Dependencies | Acceptance Criteria | Skills |
| --- | ------ | ---- | ---------------- | ------------ | ------------------- | ------ |
| 1 | DONE | Add `EnrollCfg` in `configs/enroll_cfg.py` and the `enroll` field in `Config`. Remove `PHOTOS_DIR`. Add the `enroll:` block to `config.yaml`. | developer | none | `config.load()` returns `cfg.enroll.scan_interval_s == 300` and `photos_dir == "photos"`. A value ≤ 0 for `scan_interval_s` raises a validation error. | `clean-code` |
| 2 | DONE | Write `cli/photo_scanner.py` `PhotoScanner`: folder signature, state file `scan_state.json` (next to `persons.json`), `scan_once()` (enroll changed, remove missing, save once, audit), `start()`/`stop()` thread with an interval wait. | developer | task 1 | A new folder is enrolled. An unchanged folder is skipped. A changed folder is re-enrolled. A removed folder removes the person. An empty or missing `photos/` removes everyone. Errors are logged and the thread keeps running. | `clean-code`, `security-scanner` |
| 3 | DONE | Start the scanner in `Pipeline.run()` before the loop. Stop and join it in `finally`. | developer | task 2 | `run` logs the first scan result at start. Ctrl+C exits with no hanging thread. A new folder is recognized after the next scan plus ≤ 5 s gallery reload. | `clean-code` |
| 4 | DONE | Delete `scripts/enroll.sh` and `cli/enroll_wrapper.py`. Remove the `enroll` command from `main.py` and the `__main__.py` docstring. | developer | task 3 | `python -m face_reg enroll` fails with an argparse error. `grep -r enroll_wrapper` finds nothing. `python -m face_reg run -h` still works. | `clean-code` |
| 5 | DONE | Update the docs: `README.md` (enroll section → folder sync, keep photos, delete folder = remove person), `install.sh` line 45, `PROJECT_OVERVIEW.md`, `CODING_CONVENTIONS.md`. | developer | task 4 | No doc mentions `enroll --person-id`, `--list`, `--remove`, or `enroll.sh`. The README explains `enroll.scan_interval_s`. | `clean-code` |

All 5 tasks go to **one** developer sub-agent, in order, because each one depends on the one before.
