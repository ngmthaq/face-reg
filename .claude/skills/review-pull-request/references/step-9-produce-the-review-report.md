# Step 9 — Write the Review Report

Put all results into one Markdown report. Use this template:

```markdown
## PR Review — [PR Title] (#[number])

**Author:** [author]  
**Base ← Head:** `[base-branch]` ← `[head-branch]`  
**Files changed:** [count]  
**Tests present:** Yes / No

---

### Summary

[2–4 sentences: overall quality, risk level, and if the PR is ready to merge, needs small changes, or needs big changes.]

---

### Requirements Conformance

| #   | Requirement | Status                                     | Details |
| --- | ----------- | ------------------------------------------ | ------- |
| 1   | ...         | Missing / Partial / Mismatch / Unexplained | ...     |

---

### Clean Code

#### Findings

| #   | File      | Line(s) | Principle | Description |
| --- | --------- | ------- | --------- | ----------- |
| 1   | `file.ts` | 42–55   | SRP       | ...         |

#### Suggestions

[Give clear refactors for the 3–5 most important findings.]

---

### Security

#### Findings

| #   | Severity | File      | Line(s) | Category      | Description |
| --- | -------- | --------- | ------- | ------------- | ----------- |
| 1   | HIGH     | `file.ts` | 88      | SQLi (CWE-89) | ...         |

#### Remediations

[Give code fixes for all CRITICAL and HIGH findings.]

---

### Testing _(omit section if no test files in diff)_

#### AAA Violations

| #   | File           | Test Name    | Violation                                                                 |
| --- | -------------- | ------------ | ------------------------------------------------------------------------- |
| 1   | `user.test.ts` | `test_login` | AAA violation: name describes implementation details rather than behavior |

#### Coverage Gaps

[List the new logic in the diff that has no tests.]

---

### Verdict

| Dimension    | Status                                                                           |
| ------------ | -------------------------------------------------------------------------------- |
| Requirements | ✅ Fully addressed / ⚠️ Partially addressed / ❌ Missing or mismatched           |
| Clean Code   | ✅ Approved / ⚠️ Minor issues / ❌ Major issues                                  |
| Security     | ✅ No findings / ⚠️ Low/Medium only / ❌ Critical/High findings                  |
| Testing      | ✅ Adequate / ⚠️ Gaps noted / ❌ Missing / ➖ N/A                                |
| **Overall**  | ✅ **Approve** / ⚠️ **Request Changes (minor)** / ❌ **Request Changes (major)** |
```

> - Use `✅` only when an area has no findings, or only small style issues.
> - Use `⚠️` for findings that should be fixed but do not block the merge.
> - Use `❌` when there is at least one CRITICAL/HIGH security finding, a big design problem, or no tests at all for new logic.
> - The overall verdict is the **worst** result of all the areas that apply.
