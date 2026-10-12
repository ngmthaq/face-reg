# Title: Plan — Move `modules/face_edge/` → `face_reg/` and rename to `face_reg` everywhere

- Classification: feature (refactor)
- Description: Make the project one package `face_reg/` at the repo root, with one name everywhere (underscore, never hyphen). No logic change.

---

## Target

```
face-reg/                      (repo root, not renamed)
├── face_reg/                  was modules/face_edge/
│   ├── __main__.py            python -m face_reg run | enroll
│   ├── config.yaml, src/, scripts/, deploy/, tests/, photos/, data/, README.md
│   └── deploy/face_reg.service
├── models/  plans/  pytest.ini  requirements.txt  README.md
```

## Functional Requirements

- FR1: `mv modules/face_edge face_reg` (with `data/` and `photos/`); delete the empty `modules/`.
- FR2: All imports, `python -m` paths, `prog=`, docstrings use `face_reg...` (`python -m face_reg run`, `python -m face_reg.src.tools.record`).
- FR3: `configs/config.py`: `PROJECT_ROOT = MODULE_DIR.parent`. `config.yaml` and config defaults use `face_reg/data/...`.
- FR4: Logger names `face_edge.*` → `face_reg.*`.
- FR5: `deploy/face_reg.service` (renamed): service, Linux user/group `face_reg`, install dir `/opt/face_reg`, `ExecStart ... -m face_reg run --config /opt/face_reg/face_reg/config.yaml`, `ReadWritePaths=/opt/face_reg/face_reg/data`.
- FR6: `install.sh` and `scripts/*.sh`: `cd` 2 levels up (`../..`) to the project root; `MOD=face_reg`.
- FR7: `pytest.ini` (`testpaths = face_reg`, comment updated), `.gitignore`, `.graphifyignore` (`face_reg/data/`, `face_reg/photos/`).
- FR8: Docs (`face_reg/README.md`, root `README.md`, `.claude/references/PROJECT_OVERVIEW.md`, `CODING_CONVENTIONS.md`, `photos/README.md`) describe one package, not `modules/<name>/`. No `face-edge` / `face_edge` left anywhere except `plans/`.

## Risks & Assumptions

- The repo folder itself (`face-reg/`) keeps its hyphen; outside the code.
- Old plan files in `plans/` keep old names (history).
- No backup / no git. `data/` and `photos/` (biometric data) are moved with `mv` only — nothing copied or deleted.
- Anything outside this repo that calls `python -m modules.face_edge` will stop working.

## Status

- [x] Ready to execute

## Task List

| # | Status | Task | Responsible Role | Dependencies | Acceptance Criteria | Skills |
|---|---|---|---|---|---|---|
| 1 | DONE | FR1–FR7: move folder, update code, config, scripts, deploy, root config files | developer | none | `python -m face_reg -h`, `run -h`, `enroll -h` show the same options (with `face_reg` in text); `bash -n` passes on all `.sh`; `MODULE_DIR` = `<root>/face_reg`, `PROJECT_ROOT` = `<root>`; grep `face.edge\|modules/\|modules\.` over `face_reg/src`, `scripts`, `deploy`, `config.yaml`, root config files is empty | `clean-code` |
| 2 | DONE | FR8: docs | developer | 1 | Docs show only the new layout and names; same grep over docs is empty | `clean-code` |
| 3 | DONE | Update test imports, patch targets, path strings (`modules.face_edge` → `face_reg`, `modules/face_edge/scripts` → `face_reg/scripts`); run the suite | tester | 1 | 103 passed, 5 skipped | `aaa-testing` |

Order: 1, then 2 and 3 in parallel. After: delete stale caches (`__pycache__`, `.pytest_cache`) and run `graphify update .`.
