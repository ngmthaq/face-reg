# Title: Plan — Round 1: full-path imports and install.sh excludes

- Classification: feature (refactor)
- Description: Change every relative import in `modules/face_edge/src/` to a full path. Remove the `sys.path` hack in the tools. Make `install.sh` skip the dev-only folders.

---

## Approach Summary / Goal

- Change each `from .x` and `from ..x` import to `from modules.face_edge.src...`. Keep the lazy imports inside functions where they are now (`cli.py:22,38,39`, `pipeline.py:146,227`). Only change their path.
- Remove the `sys.path.insert` hack and the `# noqa: E402` comments in `tools/`. Tools then run only with `python -m` from the project root, as the conventions say.
- Add `--exclude .git --exclude .claude --exclude graphify-out --exclude .pytest_cache` to the rsync in `deploy/install.sh`.
- Goal: the code follows CODING_CONVENTIONS, and the device gets no dev files. Behaviour does not change.

## Functional Requirements

- No relative import is left in `modules/face_edge/` (`grep -rnE "^\s*from \.+" modules/face_edge` finds nothing).
- `python -m pytest -q` gives the same result as before: 20 passed, 1 skipped.
- `python -m modules.face_edge --help` and `python -m modules.face_edge.tools.eval_offline --help` both run.
- The rsync in `install.sh` skips `.git`, `.claude`, `graphify-out` and `.pytest_cache`. It still skips `.venv`, `data`, `photos`, `__pycache__` and `config.yaml`.

## Non-Functional Requirements

- Only imports and rsync flags change. No logic changes.
- Import order: `__future__`, standard library, third-party, project. Project imports are sorted A–Z (this fixes the order at `pipeline.py:21`).

## Files in Scope

- `modules/face_edge/src/cli.py`, `enroll.py`, `pipeline.py`, `sinks.py`
- `modules/face_edge/src/stages/decide.py`, `detect.py`, `quality.py`, `recognize.py`, `tracker.py`
- `modules/face_edge/tools/eval_offline.py`, `export_liveness_onnx.py` (if it has the same hack)
- `modules/face_edge/deploy/install.sh`

## Risks & Assumptions

- Risk: `python modules/face_edge/tools/eval_offline.py` (run as a plain script path) will stop working. Only `python -m modules.face_edge.tools.eval_offline` will work. This matches the rule "run every command from the project root". The docstring already shows `python -m`.
- Assumption: the lazy imports are lazy on purpose (they skip loading cv2 GUI code and the pipeline for `enroll`), so they stay inside the functions.
- The `_redact` wrapper at `pipeline.py:226-228` is left as it is. Round 3 fixes it.

## Open Questions / Blockers

- None.

## Status

- [x] Ready to execute
- [ ] Blocked — requires user input on: —

## Task List

| # | Status | Task | Responsible Role | Dependencies | Acceptance Criteria | Skills |
|---|---|---|---|---|---|---|
| 1 | DONE | Change all relative imports in `src/` and `src/stages/` to full paths. Keep lazy imports in place. Sort the project imports. | developer | none | grep finds no `from .`; pytest gives 20 passed, 1 skipped; `python -m modules.face_edge --help` runs | `clean-code` |
| 2 | DONE | Remove the `sys.path.insert` hack and the `# noqa: E402` comments in `tools/*.py`. Make sure the docstring shows `python -m`. | developer | none | No `sys.path` in `tools/`; `python -m modules.face_edge.tools.eval_offline --help` runs | `clean-code` |
| 3 | DONE | Add rsync excludes for `.git`, `.claude`, `graphify-out` and `.pytest_cache` in `deploy/install.sh`. | developer | none | The rsync line has all 9 excludes; `bash -n install.sh` passes | none |
| 4 | DONE | Run the full test suite and the two `--help` commands. Report the results. Do not change any test files unless a test imports with a relative path. | tester | 1, 2, 3 | 20 passed, 1 skipped; both commands exit 0 | `aaa-testing` |

## Review Note

- Task 2: `tools/export_liveness_onnx.py:31` keeps `sys.path.insert(0, str(repo))`. It adds the outside Silent-Face-Anti-Spoofing repo (needed to load its PyTorch model classes), not the project root. It is not the hack this task removes. The criterion "No `sys.path` in `tools/`" should have said "no project-root `sys.path` hack".
- Review decision: accepted.
