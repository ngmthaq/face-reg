# Title: Plan — Move `face_reg/config.yaml` → root `config.yaml`

- Classification: feature (refactor)
- Description: The config file moves to the repo root; `face_reg/` holds only code. No logic change.

---

## Changes

| Area | Change |
|---|---|
| Move | `mv face_reg/config.yaml config.yaml` |
| `src/configs/config.py` | `DEFAULT_CONFIG = PROJECT_ROOT / "config.yaml"`; keep `MODULE_DIR` |
| Help text | `default: face_reg/config.yaml` → `default: config.yaml` in `pipeline_wrapper.py`, `enroll_wrapper.py`, `record.py`, `eval_offline.py`; docstrings in `main.py`, `export_liveness_onnx.py` |
| `deploy/install.sh` | rsync excludes `/config.yaml`; config copy, chown, chmod, echo use `$DST/config.yaml` |
| `deploy/face_reg.service` | `--config /opt/face_reg/config.yaml` |
| Docs | Root `README.md`, `.claude/references/*` |
| Tests | Rename `test_config_path_resolves_against_module_dir` → `test_config_path_resolves_against_project_root`; check nothing else needs a change |

## Status

- [x] Ready to execute

## Task List

| # | Status | Task | Responsible Role | Dependencies | Acceptance Criteria | Skills |
|---|---|---|---|---|---|---|
| 1 | DONE | Move + code + deploy + docs | developer | none | `face_reg/` holds only `__main__.py`, `src/`, `tests/`; `DEFAULT_CONFIG` = `<root>/config.yaml`; `python -m face_reg run -h` shows `default: config.yaml`; `bash scripts/enroll.sh --list` still lists `emp_0001`; `bash -n deploy/install.sh`; no `face_reg/config.yaml` outside `plans/` | `clean-code` |
| 2 | DONE | Suite + test rename | tester | 1 | 103 passed, 5 skipped | `aaa-testing` |
