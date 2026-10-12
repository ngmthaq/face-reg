# Step 6 — Review (Root Agent)

The Root Agent reviews the developer and tester work itself. It does not start a reviewer sub-agent. The review checks the work against the **approved plan**, the project **conventions**, **security**, and **business logic**. It is the last check before the user gets the result.

> The review is read-only. Do not edit files or write tests. Run only read-only checks and the required skill checks.

---

## Routing

| Sub-agent result                            | Root Agent action                                                                                         |
| ------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `Open Questions` present                    | Find answers in the plan/brainstorming notes, or ask the user. Then delegate again (**Step 4**) with them |
| `incomplete` or `blocked`                   | Fix the blocker (if the plan is wrong, plan again with **Step 1/2**). Then delegate again (**Step 4**)    |
| `complete` — review **not fully qualified** | Go back to **Step 4**. Start the sub-agent named in each issue's `Responsible Role` again, with feedback  |
| `complete` — review **accepted**            | Go to **Step 7** (summary report)                                                                         |

---

## Review Workflow

1. **First, check the `Status` from each sub-agent.** If a result is `incomplete` or `blocked`, or has `Open Questions`, handle that first. See the routing table above.
2. **Check against the approved plan and the user's original request.** Read the user's original prompt word for word. Read the approved plan. The work must match both. A delegation summary can drift away from what the user wanted.
3. **Look at every file in the `Files Changed` tables.** Do not trust the sub-agent summaries alone. Read the real code and tests.
4. **Check the `Acceptance Criteria` and `Verification / Checks Run` tables.** Every criterion must be `yes`. Any `no` or `partial` fails the review. Run any check marked `not-run` yourself. Also run the key checks again (always the security/secret scans). Make sure each `pass` is real. A `pass` from a sub-agent is a claim, not proof.
5. **Check project conventions.** The work must follow the naming, folder structure, patterns, frameworks, and every skill given in the delegation.
6. **Check security.** Run the skill checks (scripts) on the diff. If a check fails, the review fails.
7. **Check business logic.** Follow the changed code paths. Compare them with the plan's requirements: the behavior is correct, edge cases are handled, and there are no unwanted side effects or regressions.
8. **Check tests.** Tests must cover the needed cases (happy path, edge cases, failure cases), and they must pass. A bug fix must have a regression test.
9. **On a second review, check that each old issue is fixed.** Go through the issue list from the last review. Make sure a real change fixes each one. An issue that is still there still fails.
10. **Decide.** Use `accepted` only if every checklist item passes and there are no critical or high issues left. If not, go back to Step 4 with review feedback.

---

## Checklist

| Item                                                  | Result                |
| ----------------------------------------------------- | --------------------- |
| Satisfies the approved plan and original requirement  | pass - fail - partial |
| Every task's Acceptance Criteria met                  | pass - fail - partial |
| Verification / checks confirmed again (not just said) | pass - fail - partial |
| Follows project conventions and skill references      | pass - fail - partial |
| No unwanted side effects or regressions               | pass - fail - partial |
| Tests cover required scenarios and pass               | pass - fail - partial |
| No security, performance, or maintainability issues   | pass - fail - partial |

- There are only two results: `accepted` or `not qualified`. Never "accepted with issues".
- A `critical` or `high` issue always fails the review. The Root Agent may accept `medium` or `low` issues. But it must list them as recommendations in the summary report.
- Anything `partial` must be fixed before you accept. If not, the review fails. No quiet passes.

---

## Review Feedback (when not qualified)

For each issue, give enough detail so the sub-agent can fix it without asking questions. Add a `Responsible Role`, so the right sub-agent gets it:

| #   | Severity                       | File           | Responsible Role   | Description                      |
| --- | ------------------------------ | -------------- | ------------------ | -------------------------------- |
| 1   | critical - high - medium - low | {path/to/file} | developer - tester | {clear description of the issue} |
| …   | …                              | …              | …                  | …                                |

> **Note:** Do not write unclear feedback like "Code quality is poor". Be specific: "Function `calculateTotal` in `billing.js` has a cyclomatic complexity of 15. Our limit is 10." Paste the related rows into the `Review Feedback` section of the new delegation prompt.

---

## Rules

- **No hidden failures.** Show and fix every `incomplete`, `blocked`, or open question. Never hide one.
- The Root Agent never fixes issues itself. Every fix goes back to the responsible sub-agent.
- Loop guard: if the same work fails **2 reviews in a row**, show the results to the user. Ask if you should go on or stop.

---

## Minimum Skill References

Use at least these on every review:

- [clean-code](../../clean-code/SKILL.md) — code review checklist
- [testing-workflow](../../../agents/party-mode-tester.md#testing-workflow) — testing workflow principles
- [security-scanner](../../security-scanner/SKILL.md) — run it on the diff before any `accepted` decision. Its secrets scan (`scan-secrets.sh --diff`) must exit with `0`

Also check every other skill given in the delegations.
