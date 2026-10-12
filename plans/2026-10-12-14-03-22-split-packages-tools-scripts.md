# Title: Plan — Split config, datatypes, CLI into packages; move tools into src; add scripts/

- Classification: feature (refactor)
- Description: Move files into small packages and update every import, path, and doc. No behaviour change.

---

## Approach Summary / Goal

- The project uses **namespace packages** (no `__init__.py`, see `pytest.ini`). New folders follow the same rule: no `__init__.py`. Callers import from the exact file (e.g. `from modules.face_edge.src.configs.camera_cfg import CameraCfg`).
- File name = snake_case of the class name (`CameraCfg` → `camera_cfg.py`, `QualityResult` → `quality_result.py`).
- The CLI dispatcher lives in `src/cli/main.py` (no `__init__.py` in this project).
- Goal: smaller files and a clear layout. Same commands, same config file, same output, same tests.

## Target Layout (`modules/face_edge/`)

```
src/
├── configs/   config.py (Config, load, MODULE_DIR, PROJECT_ROOT, DEFAULT_CONFIG, PHOTOS_DIR)
│              camera_cfg.py, liveness_model_cfg.py, models_cfg.py, thresholds_cfg.py,
│              tracker_cfg.py, decision_cfg.py, relay_cfg.py
├── datatypes/ face.py, quality_result.py, frame_result.py, decision.py, track.py, event.py
├── cli/       main.py (main dispatcher + setup_logging), run.py (`run`), enroll.py (`enroll` argparse/main)
├── tools/     sinks.py, overlay.py, eval_offline.py, record.py, export_liveness_onnx.py
├── stages/    (unchanged, only imports updated)
├── enroll.py  (enroll logic only, main() moved out)
└── pipeline.py
scripts/       download_models.sh (moved), run.sh, enroll.sh, record.sh, eval.sh, test.sh
deploy/        install.sh (path to download_models.sh updated), face-edge.service (unchanged)
```

Deleted: `src/config.py`, `src/datatypes.py`, `src/cli.py`, `src/sinks.py`, `src/overlay.py`, old `modules/face_edge/tools/`.

## Functional Requirements

- FR1: `python -m modules.face_edge run [--show] [--source] [--window] [--config] [-v]` and `python -m modules.face_edge enroll ...` work as before (same options, same exit codes).
- FR2: `MODULE_DIR` still points to `modules/face_edge` (now `parents[2]`). `PROJECT_ROOT`, `DEFAULT_CONFIG`, `PHOTOS_DIR` keep their values.
- FR3: Each `*Cfg` class and each dataclass is in its own file, with the same code.
- FR4: Tools run with `python -m modules.face_edge.src.tools.<name>`. Docstrings and `prog=` in `record.py` show the new path.
- FR5: `scripts/download_models.sh` still downloads into `<project root>/models`. `deploy/install.sh` calls the new path.
- FR6: Each helper script `cd`s to the project root, uses `.venv/bin/python` if it exists (else `python3`), and passes `"$@"` through.
- FR7: Error hints that name `tools/download_models.sh` or `tools/export_liveness_onnx.py` show the new paths (`stages/detect.py`, `stages/recognize.py`, `stages/liveness.py`).
- FR8: No file still has `modules.face_edge.src.config`, `src.datatypes import`, `src.cli import`, `src.sinks`, `src.overlay`, or `face_edge.tools` (except old plan files in `plans/`).

## Non-Functional Requirements

- Python 3.10 compatible. Follows `.claude/references/CODING_CONVENTIONS.md` (full import paths, same comment style).
- No logic changes. Full test suite gives the same result: 103 passed, 5 skipped.

## Files in Scope

- Create: the `src/configs/*`, `src/datatypes/*`, `src/cli/*`, `src/tools/*`, `scripts/*` files above.
- Modify: `__main__.py`, `src/enroll.py`, `src/pipeline.py`, `src/stages/*.py`, `deploy/install.sh`, all 6 files in `tests/`, `modules/face_edge/README.md`, root `README.md`, `.claude/references/PROJECT_OVERVIEW.md`, `.claude/references/CODING_CONVENTIONS.md`.
- Delete: old files listed above.

## Risks & Assumptions

- No backup (user choice). The folder is not a git repo, so undo is only by hand.
- Assumption: snake_case file names as above.
- Assumption: `deploy/install.sh` stays in `deploy/` (user choice).
- Risk: `tests/test_characterization.py` and `tests/test_security.py` call `enroll.main()`. After the move they must import `main` from `src/cli/enroll.py`.
- Old plan files in `plans/` keep the old paths (history, not changed).

## Open Questions / Blockers

- None.

## Status

- [x] Ready to execute

## Task List

| # | Status | Task | Responsible Role | Dependencies | Acceptance Criteria | Skills |
|---|---|---|---|---|---|---|
| 1 | DONE | Create `src/configs/` (7 Cfg files + `config.py` with `Config`, `load`, constants using `parents[2]`) and `src/datatypes/` (6 files). Update imports in `src/` and old `tools/*.py`. Delete `src/config.py`, `src/datatypes.py`. | developer | none | No source file imports `src.config` / `src.datatypes` as a module; `python -c "from modules.face_edge.src.configs.config import load, MODULE_DIR; print(MODULE_DIR)"` prints `.../modules/face_edge`. | `clean-code` |
| 2 | DONE | Split `src/cli.py` into `src/cli/main.py` (dispatcher + `setup_logging`), `src/cli/run.py` (`run` parser + run), `src/cli/enroll.py` (moves `main()` out of `src/enroll.py`). Update `__main__.py`. Delete `src/cli.py`. | developer | 1 | `python -m modules.face_edge -h`, `run -h`, `enroll -h` show the same options as before; `src/enroll.py` has no argparse `main`. | `clean-code` |
| 3 | DONE | Move `sinks.py`, `overlay.py` → `src/tools/`; move `tools/eval_offline.py`, `record.py`, `export_liveness_onnx.py` → `src/tools/`. Update all imports, docstrings, `prog=`, and error hints in `stages/`. | developer | 2 | `python -m modules.face_edge.src.tools.record -h` and `...eval_offline -h` work; FR8 grep is empty for `src/`. | `clean-code` |
| 4 | DONE | Create `scripts/`: move `download_models.sh`, add `run.sh`, `enroll.sh`, `record.sh`, `eval.sh`, `test.sh` (FR6). Update `deploy/install.sh`. Update both READMEs, `PROJECT_OVERVIEW.md`, `CODING_CONVENTIONS.md` (folder tree, run commands, import example). Remove the empty old `tools/` folder. | developer | 3 | `bash -n` passes on every `.sh`; scripts are executable; docs show only new paths. | `clean-code` |
| 5 | DONE | Update imports in all 6 test files, including `monkeypatch` strings (`src.tools.sinks...`) and `enroll.main` → `src.cli.enroll`. Run the full suite. | tester | 3 | `pytest` → 103 passed, 5 skipped; no test logic changed. | `aaa-testing` |

Order: 1 → 2 → 3 in sequence (same files). 4 and 5 in parallel after 3. After review: `graphify update .`.
