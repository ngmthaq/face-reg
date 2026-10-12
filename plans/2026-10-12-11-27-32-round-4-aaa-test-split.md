# Title: Plan — Round 4: AAA test split and coverage report

- Classification: feature (tests)
- Description: Split the old tests that run more than one action, so each test checks one behaviour. Add pytest-cov to report coverage before and after.

---

## Approach Summary / Goal

- A developer adds `pytest-cov` to `requirements.txt` under `# dev` and installs it in `.venv`. This is not a test file, so the tester cannot do it.
- The tester records the coverage of `modules/face_edge/src` before the change. Then the tester splits the old tests with the AAA rules, using `parametrize` and fixtures. Each split test keeps the same checks, so no check is lost.
- The tester records coverage again afterwards. It should be the same or higher.
- Goal: each test has one Act, a clear name (`<unit>_<case>_<result>`), and a clear failure message.

## Functional Requirements

1. These tests in `test_core.py` are split or turned into parametrized tests, with one Act per test:
   - `test_unknown_needs_five_live_frames`, `test_iou`, `test_tracker_keeps_id_and_drops_after_max_missed`, `test_tracker_two_people`
   - `test_yaw_frontal_and_turned`, `test_quality_reasons`, `test_gallery_top2_is_per_person`
   - `test_jsonl_and_snapshot`, `test_retention_cleanup`, `test_config_resolves_paths`, `test_angle_from_file_name`
   - and any other test with more than one Act
2. In `test_models.py`:
   - `_cfg` becomes a pytest fixture.
   - `test_pipeline_runs_on_blank_frames` has one Act.
   - `test_liveness_and_recognition_on_samples` is split into a liveness real test, a liveness spoof test (parametrized) and a recognition test. Shared setup goes in fixtures. They stay skipped when `FACE_EDGE_SAMPLES` is not set.
3. Every assertion that exists today still exists after the split. The tester lists old test → new tests in the result.
4. Test names say the expected result. Use blank lines to separate Arrange, Act and Assert. Do not add `# Arrange` comments.
5. A real bug found while splitting → `@pytest.mark.xfail(strict=True, reason=...)` plus a report. Production code is not changed.

## Non-Functional Requirements

- `test_characterization.py` and `test_security.py` are not changed.
- The full suite stays fast (under 5 s).

## Files in Scope

- `requirements.txt` (add `pytest-cov>=4`)
- `modules/face_edge/tests/test_core.py`
- `modules/face_edge/tests/test_models.py`

## Risks & Assumptions

- Assumption: `pip install` can reach PyPI from this machine.
- The test count goes up because of the splits and parametrize. The number of checks stays the same.
- Groups B and C (new tests for stream, cli, overlay and the stages) are not in this round. The coverage report will show these gaps.

## Open Questions / Blockers

- None.

## Status

- [x] Ready to execute
- [ ] Blocked — requires user input on: —

## Task List

| # | Status | Task | Responsible Role | Dependencies | Acceptance Criteria | Skills |
|---|---|---|---|---|---|---|
| 1 | DONE | Add `pytest-cov>=4` to `requirements.txt` under `# dev`. Run `.venv/bin/pip install -r requirements.txt`. | developer | none | `.venv/bin/python -c "import pytest_cov"` works; full suite still passes | none |
| 2 | DONE | Record a baseline: `pytest --cov=modules/face_edge/src --cov-report=term-missing -q`. Split the tests in FR 1 and FR 2. Run the coverage again. Report the old → new test mapping and both coverage totals. | tester | 1 | Full suite passes; every old assertion kept; one Act per test; coverage after ≥ before; `test_characterization.py` and `test_security.py` unchanged | `aaa-testing` |

## Review Note

- Review 1 (not qualified): Acts hidden inside asserts in the gallery tests (medium); a 156-char line; repeated `128`. The tester fixed these and the same pattern in about 20 other tests.
- Review 2: accepted. 81 passed, 5 skipped. Coverage of `modules/face_edge/src`: 74% before and after (1147 statements, 301 missed). Secrets scan: no secrets.
- Side effect: `pip install -r requirements.txt` upgraded opencv-python-headless to 5.0.0.93 (allowed by `>=4.8`).
