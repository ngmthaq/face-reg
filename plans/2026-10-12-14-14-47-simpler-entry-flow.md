# Title: Plan — Simpler entry flow (`__main__.py` → `src/main.py` → `src/cli/*`)

- Classification: feature (refactor)
- Description: Move the dispatcher to `src/main.py`, rename `cli/run.py` to `cli/pipeline.py`, move `setup_logging` to `src/tools/logs.py`. No logic change; command name stays `run`.

---

## Changes

| Change | Detail |
|---|---|
| New `src/tools/logs.py` | `setup_logging` moves here, unchanged |
| `src/cli/main.py` → `src/main.py` | Same dispatcher; imports `setup_logging` from `src.tools.logs`; lazy-imports `cli.pipeline` (as it does `cli.run` today) |
| `src/cli/run.py` → `src/cli/pipeline.py` | Same code (`add_run_parser`, `run_command`) |
| `__main__.py` | `from modules.face_edge.src.main import main` |
| `src/tools/record.py`, `src/tools/eval_offline.py` | Import `setup_logging` from `src.tools.logs` |
| Docs | `modules/face_edge/README.md:134` and `.claude/references/PROJECT_OVERVIEW.md:38` (cli line; add `src/main.py`, `tools/logs.py`) |

## Status

- [x] Ready to execute

## Task List

| # | Status | Task | Responsible Role | Dependencies | Acceptance Criteria | Skills |
|---|---|---|---|---|---|---|
| 1 | DONE | All changes above; delete `src/cli/main.py`, `src/cli/run.py` | developer | none | Top-level, `run`, `enroll` `-h` identical to before; `record -h`, `eval_offline -h` work; no file mentions `cli.main`, `cli/main`, `cli.run`, `cli/run.py` | `clean-code` |
| 2 | DONE | Full suite; confirm no test uses an old path (no edits expected) | Root Agent check | 1 | 103 passed, 5 skipped | — |
