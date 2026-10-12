# Step 4 — Triage and Group Comments

Turn the comments from Step 3 into a clean list of **tasks**. In Step 5, you give this list to party-mode as the requirement.

## Remove comments that need no work

Skip a comment in these cases. Write down why, for the Step 7 report.

- **Already resolved** or **outdated** (its line no longer exists).
- **Only praise or a thank-you** ("nice", "LGTM", "thanks").
- **A question that asks for no change.** Write a reply for Step 6. Do not change code.
- **Out of scope** for this PR (e.g. "we should refactor the whole module someday").
- **Unclear.** You cannot link it to a real change. Tell the user. Do not guess.

Never make up what the reviewer wants. Some comments clearly ask for a change, but it is not clear what change. Pass these to party-mode's brainstorming step as an **open question**. Do not guess the fix.

## Classify each comment that needs work

Mark each one as:

- `bug` — the reviewer found something wrong or broken.
- `feature` — the reviewer asks for an improvement, refactor, naming change, or behavior change.

Party-mode uses this to know the type of work.

## Group related comments

Put comments about the same file, function, or topic into one task. Then one sub-agent can fix them together. Keep the comment IDs with each task. Step 6 needs them to reply and resolve.

## Write the triage table

```markdown
| #   | File        | Line | Author    | Request (summary)                        | Class   | Action      | Comment IDs |
| --- | ----------- | ---- | --------- | ---------------------------------------- | ------- | ----------- | ----------- |
| 1   | `user.ts`   | 42   | @reviewer | Extract validation into its own function | feature | resolve     | 1234        |
| 2   | `user.ts`   | 88   | @reviewer | Use parameterized query (SQL injection)  | bug     | resolve     | 1235        |
| 3   | `README.md` | 10   | @reviewer | "nice catch"                             | —       | skip-praise | 1236        |
| 4   | `api.ts`    | 5    | @reviewer | "could we cache this?" (question)        | —       | reply-only  | 1237        |
```

Show this table to the user. Wait for the user to confirm it before you go on.

- `resolve` rows are the work to do.
- `reply-only` rows get a reply in Step 6.
- `skip-*` rows go in the Step 7 report.
