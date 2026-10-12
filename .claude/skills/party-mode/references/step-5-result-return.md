# Step 5 — Sub-Agent Result Return

The developer and tester sub-agents send back their results with the **sub-agent result template** below.

If a sub-agent needs more information to go on, it does not guess. It sends back the result and fills in the `Open Questions` section. The Root Agent finds the answers in the approved plan and the brainstorming notes. If the answer is not written down, it asks the user. Then it starts the sub-agent again with the answers.

---

## Sub-Agent Result Template

```md
# Title: Result — {short title that matches the original delegation title}

- From: developer | tester (the `party-mode-developer` or `party-mode-tester` sub-agent)
- To: Root Agent
- Classification: feature | bug
- Description: {one sentence: what was done, or why it is not finished}

---

## Goal

- {Repeat the goal of this task, so the result is clear on its own.}

## Status

- [ ] complete
- [ ] incomplete — reason: {short reason}

## Work Summary

{2–4 sentences about what was done. Name the functions, file paths, and tests.}

## Files Changed

| File           | Action                       | Notes                        |
| -------------- | ---------------------------- | ---------------------------- |
| {path/to/file} | created - modified - deleted | {short note on what changed} |
| …              | …                            | …                            |

## Tasks Completed

| #   | Task               | Outcome                  |
| --- | ------------------ | ------------------------ |
| 1   | {task description} | done - skipped - blocked |
| …   | …                  | …                        |

## Test Results (tester sub-agent only)

| Test        | Type                     | Result                |
| ----------- | ------------------------ | --------------------- |
| {test name} | unit - integration - e2e | pass - fail - skipped |
| …           | …                        | …                     |

## Verification / Checks Run

| Check                                        | Command / How          | Result                |
| -------------------------------------------- | ---------------------- | --------------------- |
| {build - lint - test - secret-scan - manual} | {command run or steps} | pass - fail - not-run |
| …                                            | …                      | …                     |

## Acceptance Criteria

| Task # | Criterion                   | Met                |
| ------ | --------------------------- | ------------------ |
| 1      | {criterion from delegation} | yes - no - partial |
| …      | …                           | …                  |

## Open Questions

{List every question the Root Agent (or the user) must answer before the work can go on. For each one, name the task, the decision needed, and the options (if any). Never guess — ask.}

- Leave empty if none.

## Blockers / Missing Requirements

{List everything that stopped you from finishing. Be exact. Unclear blockers cause extra planning rounds.}

- Leave empty if status is complete.

## Notes for Root Agent

{Optional: things you noticed, risks, or next steps the Root Agent should know.}
```

---

## Usage Notes

- Always set Status to `complete` or `incomplete`. Nothing in between.
- If `incomplete`, you must fill in `Blockers`. The Root Agent uses it to start the sub-agent again or change the plan.
- If there are any `Open Questions`, Status must be `incomplete`. The Root Agent answers them (and asks the user if needed). Then it starts the sub-agent again with the answers.
- The `Files Changed` table must be full and correct. The review in Step 6 uses it.
- `Verification / Checks Run` must list **every** check you really ran (build, lint, tests, secret/security scan, manual steps). Add the command and the result for each one.
- Give a reason for every `not-run` row. The Root Agent uses this table so it does not have to run everything again.
- If any check is `fail`, Status must be `incomplete`.
- In `Acceptance Criteria`, copy each task's criteria from the delegation. Mark each one `yes`, `no`, or `partial`. Any `no` or `partial` means the task is not done. Set Status to `incomplete`.
- Do not mark `complete` if you skipped a task with no clear reason.
