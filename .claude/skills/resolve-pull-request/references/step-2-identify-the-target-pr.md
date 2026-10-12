# Step 2 — Identify the Target PR

Find the PR with the comments to fix. Try these in order:

1. **The user gave a PR number or URL** → use that PR.
2. **A PR is open in the editor** (MCP only) → use the MCP tool that returns it.
3. **The current branch has a PR** → use the PR for the branch you are on now.
4. **No PR found** → ask the user: _"Which PR should I fix comments on? Please give a PR number or URL."_

## Using MCP

Use the MCP tool that gets a PR by number or URL, or the one that returns the PR open in the editor.

## Using the CLI

| Platform  | Find PR by number/URL                     | Current branch's PR     |
| --------- | ----------------------------------------- | ----------------------- |
| GitHub    | `gh pr view <number-or-url> --json ...`   | `gh pr view --json ...` |
| GitLab    | `glab mr view <number-or-url>`            | `glab mr view`          |
| Bitbucket | `bb pr view <number>` (flags vary by CLI) | per-CLI                 |

Get these from the PR:

- Number, title, author
- Base branch and **head branch** (you must switch to this branch before you fix anything)
- The head commit SHA (you need it to reply to comments on lines)
- If the PR is open and can be merged

> Tip (GitHub): `gh pr view <n> --json number,title,headRefName,baseRefName,headRefOid,state` gets all these in one call.

## Using the browser

- **PR number or URL given** → open the PR page (see the URL table in [Step 1](./step-1-verify-access-method.md)).
- **Current branch's PR** → open the PR list filtered by your branch. On GitHub: `https://github.com/<owner>/<repo>/pulls?q=is:pr+head:<branch>`. On GitLab: `.../-/merge_requests?source_branch=<branch>`. On Bitbucket, ask the user for the PR number.
- Read the number, title, author, branches, and state from the page.
- Get the head commit SHA with git, not the browser: `git fetch origin <head-branch>` then `git rev-parse origin/<head-branch>`.
