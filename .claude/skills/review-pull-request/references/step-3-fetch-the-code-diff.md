# Step 3 — Fetch the Code Diff

Get the full diff (changed files) of the PR. Use the access method from Step 1.

## Using MCP

Use the MCP tool that gets the diff or changed files.

## Using the CLI

| Platform  | Diff command                                |
| --------- | ------------------------------------------- |
| GitHub    | `gh pr diff <number-or-url>`                |
| GitLab    | `glab mr diff <number-or-url>`              |
| Bitbucket | `bb pr diff <number>` (flags differ by CLI) |

## Using the browser

Get the diff with git first. It is faster and more exact than reading the page:

```bash
git fetch origin <base-branch> <head-branch>
git diff origin/<base-branch>...origin/<head-branch>
```

If git cannot get the branches (e.g. the PR comes from a fork), open the **Files changed** tab (GitHub) or the **Changes** tab (GitLab) and read the diff there. Expand any files that are hidden or collapsed.

**Large diffs (more than 400 changed lines):** sum up by file or module, not line by line.

From the diff, find:

- Which files are changed, added, or deleted
- If there are test files (e.g. `*.test.*`, `*.spec.*`, `*_test.*`, or files in `tests/`, `__tests__/`, `spec/`)
- The languages and frameworks used

> Keep the diff parts with their line numbers. Step 10 posts comments on exact files and lines. So you need the new line number for each finding.
