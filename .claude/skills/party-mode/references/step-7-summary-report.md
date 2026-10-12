# Step 7 — Summary Report to User

When the review is `accepted`, the Root Agent sends a report to the user **as a chat message**. Use the template below. Take every fact from the sub-agent results (Step 5) and the review (Step 6). Do not make anything up.

---

## Summary Report Template

```md
# Title: Summary — {short title that matches the original request}

- Classification: feature | bug
- Description: {one sentence about what was done}

---

## Goal

- {The goal that was reached — what the user asked for. For a bug, name the root cause that was fixed, not just the symptom.}

## What Changed

{2–4 sentences about what was done. For a bug, name the root cause that was fixed, not just the symptom.}

## Files Changed

| File           | Action                       | Notes                        |
| -------------- | ---------------------------- | ---------------------------- |
| {path/to/file} | created - modified - deleted | {short note on what changed} |

## Tests

| Test        | Type                     | Result         |
| ----------- | ------------------------ | -------------- |
| {test name} | unit - integration - e2e | pass - skipped |

## Verification

- {Checks that ran and their results: build, lint, tests, secret/security scan. Copy them from the `Verification / Checks Run` tables in the sub-agent results.}

## Review Outcome

- Decision: accepted
- Recommendations (`medium`/`low` issues that do not block, left for later): {list, or "none"}

## Follow-ups / Notes

- {Open items, risks, or next steps — or "none".}
```

---

## Usage Notes

- Every row comes from the sub-agent results and the review. The report only puts them together. It is not new work. If a fact is not written down, say so. Do not guess.
- **Tests** and **Verification** must show only what really ran. If no `Verification / Checks Run` table lists a check, do not say it passed.
- List every `medium`/`low` issue that the review accepted under **Recommendations**. Then the user can decide what to do next.
- After the report, update the `Status` column in the `## Task List` section of the plan file. Show the final state of each task (`DONE`, `SKIPPED`, etc.).
