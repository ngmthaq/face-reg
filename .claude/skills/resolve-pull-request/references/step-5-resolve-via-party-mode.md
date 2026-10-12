# Step 5 — Resolve via Party-Mode

The **party-mode** workflow makes the real fixes. The Root Agent never edits files itself. Developer/tester sub-agents make every change. Then the Root Agent reviews it.

## Check out the PR branch first

Before any fix, switch to the PR's head branch (from Step 2):

```bash
gh pr checkout <number>     # GitHub
# or: git fetch origin <head-branch> && git switch <head-branch>
```

Check that there are no uncommitted changes before you delegate.

## Hand the triage list to party-mode

Load the [party-mode](../../party-mode/SKILL.md) skill and run it. Use the **`resolve` rows from the Step 4 triage table** as the requirement. Here is how each party-mode step works here:

1. **Brainstorming** — Use each reviewer request as the requirement. Answer each open question with the user, or by reading the comment again. Mark each as `feature` or `bug`, using the Step 4 tags.
2. **Planning** — The Root Agent writes a plan. Its **Task List** has one task per reviewer request (or per group). Each task has a `Responsible Role` (developer or tester) and the **comment IDs**.
3. **Approval gate** — Show the plan. **Wait for the user to clearly approve it.** Make no fix before that. This step is required.
4. **Delegation** — Start developer/tester sub-agents to make the changes. Run tasks that do not depend on each other at the same time.
5. **Result return + Review** — The Root Agent checks every result against the reviewer's comment, the project conventions, and the plan. If a task does not fully fix its comment, delegate it again.
6. **Summary** — party-mode reports the result of each task back to this skill.

## Pass-through rules

- Every party-mode task must link to one or more **comment IDs**. Then Step 6 can reply to the right threads.
- A reviewer request is "done" only when both are true: the Root Agent's review accepts the change, **and** the change really does what the comment asked. Just changing some code is not enough.
- Party-mode's loop guard may stop a task that is still `incomplete` or `blocked`. Report that task. Do not resolve its thread in Step 6.
