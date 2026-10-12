# Step 7 — Summary Report

After you reply to and resolve the threads, send a report to the user.

The report must have:

- **Resolved** — each fixed comment: the file + line, one line about the fix, and the commit(s).
- **Replied (no code change)** — questions or notes you answered with no code change.
- **Skipped** — comments you did not act on, each with the reason (already resolved, outdated, praise, out of scope, unclear).
- **Outstanding** — comments whose fix was `incomplete` / `blocked` in party-mode, and threads left open. Say why. Show these clearly. Never hide them.
- **PR state** — the pushed branch, the PR/MR link, and counts (resolved / replied / skipped / outstanding).

## Suggested format

```markdown
## Resolve Summary — PR #<number>

**Resolved (N):**
| File | Line | Fix | Comment ID |
| ---- | ---- | --- | ---------- |
| `user.ts` | 88 | Switched to parameterized query | 1235 |

**Replied, no code change (N):**
| File | Line | Reply | Comment ID |
| ---- | ---- | ----- | ---------- |

**Skipped (N):**
| File | Line | Reason | Comment ID |
| ---- | ---- | ------ | ---------- |

**Outstanding (N):**
| File | Line | Status | Notes | Comment ID |
| ---- | ---- | ------ | ----- | ---------- |
```

If party-mode wrote a plan file, update its `Status` column. Show if each task is resolved or outstanding.
