# Step 2 — Planning (Root Agent)

When brainstorming has answered every open question, the Root Agent writes the plan **itself**. Do not start a planner or debugger sub-agent. The plan splits the work into small tasks. Show the plan to the user **as a chat message**. The user must approve it (Step 3) before any code is written.

> Planning is read-only. Do not edit files. Only run commands that read things, never commands that change things. **DO NOT** save the plan to the Doc Directory in this step. The plan is saved to a file only in [Step 3 — User Approval Gate](./step-3-approval-gate.md), after the user approves.

---

## Planning Rules

1. **Plan only when the requirement is clear.** Do not start while any question from [Step 1 — Brainstorming](./step-1-brainstorming.md) is still open.
2. **Use every related skill** you found in brainstorming. Do not plan from memory or guesses.
3. **Link the requirement to real files and modules.** Use real paths. Do not make up files.
4. **Split the work into small tasks.**
   - One sub-agent must be able to finish each task in one go.
   - Each task must name a file, a function, or a clear output.
   - Each task must have acceptance criteria you can test.
   - Do not write unclear tasks like "Refactor codebase".
5. **Set the role for each task** (`developer` or `tester`) in the `Responsible Role` column. Then you can build the delegation prompts straight from the task list.
6. **List risks and assumptions.** Anything you guessed from context, that the user did not say, goes here.
7. **Follow the existing code style.** Use the same patterns, frameworks, and folder structure as the codebase.

### Additional rules for `bug` plans

- **Fix the root cause, not only the symptom.** Every fix plan must explain why the bug happens, not only how to stop it. A plan that hides the symptom without the real cause is not complete.
- **A regression test is required.** Every fix plan must have a tester task that adds a test. The test must fail on the old (buggy) code and pass after the fix.
- **Do not break existing behaviour.** List the callers, edge cases, and related code the fix may affect. Point out any risk of breaking old behaviour (backward compatibility).
- **More than one possible root cause?** Do not pick one without telling the user. Go back to brainstorming. Ask the user which one matches what they saw.

---

## Plan Template

Show the full plan to the user **in a chat message** with this template. Do not save it to a file yet. Fill in every section.

```md
# Title: Plan — {short title matching the original request}

- Classification: feature | bug
- Description: {one sentence about the approach}

---

## Approach Summary / Goal

- {2–4 short sentences: how you will build or fix it, and why you chose this way.}
- {For a bug: the real root cause, not only the symptom.}
- {Goal}

## Functional Requirements

- {What the feature or fix must do for this plan to succeed. Each item must be testable.}

## Non-Functional Requirements

- {Needs about speed, security, ease of maintenance, or other quality needs.}

## Files in Scope

- {All files you expect to create, change, or delete}

## Risks & Assumptions

- {Assumptions you made while planning}
- {Risks the user should know about}

## Open Questions / Blockers

> **Rule: ALWAYS tell the user about anything unclear. Never guess.**
> If any task, requirement, or design choice is still unclear, list it here and go back to brainstorming. Do not start work while blockers are open.

- {Questions the user must answer before work starts}
- {Blockers that stop a task from being planned correctly}
- Leave empty if none.

## Status

- [ ] Ready to execute
- [ ] Blocked — requires user input on: {describe each blocker clearly}

## Task List

{Ordered list of small tasks. Each task belongs to one sub-agent.}

| #   | Status | Task               | Responsible Role | Dependencies | Acceptance Criteria    | Skills        |
| --- | ------ | ------------------ | ---------------- | ------------ | ---------------------- | ------------- |
| 1   | WIP    | {task description} | developer        | none         | {what done looks like} | `clean-code`  |
| 2   | TODO   | {task description} | tester           | task 1       | {what passing means}   | `aaa-testing` |
| …   | …      | …                  | …                | …            | …                      | …             |

> **Note:** Tasks must be small and clear. Do not write unclear tasks like "Refactor codebase". Split them into exact changes to files or functions. Each task must have:
>
> - a `Responsible Role` (developer or tester), so the Root Agent can build delegation prompts straight from the task list;
> - testable `Acceptance Criteria` (copied as-is into the delegation's `Tasks Assigned` table, and checked again at Step 6);
> - the related skills to use for the task.

> **Note:** The Status values in `Task List` are:

- `TODO` — not started yet
- `WIP` — in progress
- `BLOCKED` — cannot move on because of an open issue (link to the blocker in the Blockers section)
- `SKIPPED` — left out on purpose in this round (say why)
- `DONE` — finished
```

---

## Usage Notes

- Every task in the Task List must have a `Responsible Role` (developer or tester). The Root Agent picks the matching rows to build the [developer](../../../agents/party-mode-developer.md#delegation-prompt-template) and [tester](../../../agents/party-mode-tester.md#delegation-prompt-template) delegation prompts.
- **ALWAYS set Status to `Blocked` and list every open question** when anything is unclear. Do not plan around missing information. Do not guess. Go back to [Step 1 — Brainstorming](./step-1-brainstorming.md) and solve them with the user.
- The Root Agent **MUST** show the full plan to the user **as a chat message only**. Do not write it to the Doc Directory in this step. **ALWAYS read [Step 3 — User Approval Gate](./step-3-approval-gate.md)**. It says how to handle the user's choice and when to save the plan to a file.
- If Status is `Blocked`, the Root Agent must ask the user before going to Step 4. Do not start work with open blockers.
- At Step 6 the Root Agent checks the finished work against this plan. So keep requirements and acceptance criteria exact enough to check.

---

## Minimum Skill References

Use these on every plan, at least:

- [clean-code](../../clean-code/SKILL.md) — code quality rules to follow in the plan
- [testing-workflow](../../../agents/party-mode-tester.md#testing-workflow) — testing workflow rules

Also use any other skills you found in brainstorming.
