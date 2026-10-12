# Step 2 — Identify the Target PR

Find the PR to review. Use this order:

1. **The user gave a PR number or URL** → get that PR.
2. **A PR is open in the editor** (MCP only) → use the MCP tool that returns it.
3. **No PR found** → ask the user: _"Which PR should I review? Please give a PR number or URL."_

## Using MCP

Use the MCP tool that gets a PR by number/URL, or the one that returns the PR open in the editor.

## Using the CLI

| Platform  | Get PR by number/URL                        | PR of the current branch |
| --------- | ------------------------------------------- | ------------------------ |
| GitHub    | `gh pr view <number-or-url> --json ...`     | `gh pr view --json ...`  |
| GitLab    | `glab mr view <number-or-url>`              | `glab mr view`           |
| Bitbucket | `bb pr view <number>` (flags differ by CLI) | depends on the CLI       |

Get these from the PR:

- Title and description (body)
- Author, base branch, head branch
- Labels and linked issues (if any)

> Tip (GitHub): `gh pr view <n> --json number,title,body,author,baseRefName,headRefName,labels` gets all of these in one call.

## Using the browser

Open the PR page (see the URL table in [Step 1](./step-1-verify-mcp-availability.md)). Read the items above from the page. If the user gave no PR number or URL, ask for one.
