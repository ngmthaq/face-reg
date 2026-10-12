# Title: Plan — Move pipeline.py and enroll.py into cli/, rename CLI files to *_wrapper.py

- Classification: feature (refactor)
- Description: `src/pipeline.py` → `src/cli/pipeline.py`, `src/enroll.py` → `src/cli/enroll.py`; current CLI files become `pipeline_wrapper.py` / `enroll_wrapper.py`. No logic change.

---

## Flow

```
__main__.py
  └─ src/main.py
       ├─ src/cli/pipeline_wrapper.py  → src/cli/pipeline.py   (command: run)
       └─ src/cli/enroll_wrapper.py    → src/cli/enroll.py     (command: enroll)
```

## Changes

| Step | Change |
|---|---|
| 1 | Rename `src/cli/pipeline.py` → `src/cli/pipeline_wrapper.py`, `src/cli/enroll.py` → `src/cli/enroll_wrapper.py` |
| 2 | Move `src/pipeline.py` → `src/cli/pipeline.py`, `src/enroll.py` → `src/cli/enroll.py` (code unchanged) |
| 3 | Update imports: `src/main.py`, both wrappers, `src/tools/eval_offline.py` |
| 4 | Docs: folder tree in `modules/face_edge/README.md`, `PROJECT_OVERVIEW.md` |
| 5 | Tests: `enroll_cli.main` → `src.cli.enroll_wrapper`; patches on `src.enroll` / `src.pipeline` → `src.cli.enroll` / `src.cli.pipeline` |

## Status

- [x] Ready to execute

## Task List

| # | Status | Task | Responsible Role | Dependencies | Acceptance Criteria | Skills |
|---|---|---|---|---|---|---|
| 1 | DONE | Steps 1–4 | developer | none | Top-level, `run`, `enroll` `-h` identical; `eval_offline -h` works; no file mentions `src.pipeline`, `src.enroll`, `src/pipeline.py`, `src/enroll.py` | `clean-code` |
| 2 | DONE | Step 5; confirm each patch still takes effect | tester | 1 | 103 passed, 5 skipped | `aaa-testing` |
