# Title: Plan — Rename `cli/` → `entry/` and number the files by step

- Classification: refactor
- Description: Make the call order easy to see from file names. `entry/` files get `step_N_` in call order from `main.py`. `stages/` files get `step_N_` in pipeline order (the numbers already in their docstrings). No logic change.

---

## Target

```
face_reg/
├── main.py
├── entry/                         was cli/
│   ├── step_1_pipeline_wrapper.py run command, called by main.py
│   ├── step_2_pipeline.py         wires the stages
│   ├── step_3_photo_scanner.py    syncs the gallery with photos/
│   └── step_4_enroll.py           gallery logic
└── stages/
    ├── step_1_stream.py
    ├── step_2_detect.py
    ├── step_3_tracker.py
    ├── step_4_quality.py
    ├── step_5_liveness.py
    ├── step_6_recognize.py
    └── step_7_decide.py
```

## Functional Requirements

- FR1: `git mv` the folder and files as shown above.
- FR2: Update all imports (`face_reg.cli.x` → `face_reg.entry.step_N_x`, `face_reg.stages.x` → `face_reg.stages.step_N_x`).
- FR3: Docs: `README.md`, `.claude/references/PROJECT_OVERVIEW.md`, `.claude/references/CODING_CONVENTIONS.md` (new naming rule for `entry/` and `stages/`).

## Risks & Assumptions

- `stages/step_1_stream.py` uses `getLogger(__name__)`, so its logger name changes to `face_reg.stages.step_1_stream`. Nothing filters on it.
- Class and function names do not change.
- Old plan files keep old names (history).

## Status

- [x] Ready to execute

## Task List

| # | Status | Task | Responsible Role | Dependencies | Acceptance Criteria | Skills |
|---|---|---|---|---|---|---|
| 1 | DONE | FR1–FR2: rename and update imports | developer | none | `python -m face_reg -h` and `run -h` work; every module imports; grep for old module paths outside `plans/` is empty | `clean-code` |
| 2 | DONE | FR3: docs | developer | 1 | Docs show only the new names | `clean-code` |

After: delete stale `__pycache__` folders and run `graphify update .`.
