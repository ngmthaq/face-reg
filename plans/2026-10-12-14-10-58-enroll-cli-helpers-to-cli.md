# Title: Plan — Move enroll CLI helpers into cli/enroll.py

- Classification: feature (refactor)
- Description: `src/enroll.py` keeps only enroll logic; all printing, exit codes, and argparse code move to `src/cli/enroll.py`. No behaviour change.

---

## Changes

1. Move `_cmd_list`, `_cmd_remove`, `_cmd_batch`, `_cmd_enroll` from `src/enroll.py` to `src/cli/enroll.py` (they stay private there, keep the `_` prefix). `argparse` / `sys` imports leave `src/enroll.py`.
2. Two helpers stay in `src/enroll.py` but are now called from another module, so they become public: `_audit` → `audit`, `_expand` → `expand_photos`. `cli/enroll.py` calls them as `enroll_mod.audit(...)` / `enroll_mod.expand_photos(...)`, so a test patch on `src.enroll` still works.
3. The long usage docstring (command examples) moves to `cli/enroll.py`. `src/enroll.py` gets a short docstring: "Enroll logic: check photos and add face vectors to the gallery." `enroll -h` help text stays the same.

Stays in `src/enroll.py`: `EnrollResult`, `Enroller`, `angle_of`, `audit`, `expand_photos`, `IMAGE_EXT`, `ANGLES`, `ANGLE_RE`, `PERSON_ID_RE`, yaw constants.

## Risks

- Small. `src/tools/eval_offline.py` imports only `IMAGE_EXT`.

## Status

- [x] Ready to execute

## Task List

| # | Status | Task | Responsible Role | Dependencies | Acceptance Criteria | Skills |
|---|---|---|---|---|---|---|
| 1 | DONE | Changes 1–3 above | developer | none | `src/enroll.py` has no `argparse`, `print`, or `_cmd_`; `enroll -h` output is the same as before | `clean-code` |
| 2 | DONE | `test_security.py:107` patch `enroll.audit` instead of `enroll._audit`; fix any other renamed names; run suite | tester | 1 | 103 passed, 5 skipped | `aaa-testing` |
