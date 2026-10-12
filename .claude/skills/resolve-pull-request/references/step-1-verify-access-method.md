# Step 1 — Verify Access Method (MCP, CLI, or Browser)

Choose how to read review comments, push changes, and post replies. Try the options in this order. The method must be able to **read review comments**. It must also be able to **reply to and resolve** them.

## Tier 1 — Platform MCP (best)

Look for an MCP tool that can:

- Get a PR/MR by number or URL (or the PR that is open in the editor now)
- Read the PR **review comments / discussion threads** (file + line, text, author, resolved or not)
- Reply to a review thread and mark it resolved

If you find one → use **MCP** for all next steps.

## Tier 2 — Platform CLI (backup)

If there is no such MCP tool, find the platform from the remote URL. Then check for its CLI:

```bash
git remote get-url origin
```

| Remote pattern  | Platform  | CLI    | Availability check                                 | Auth check         |
| --------------- | --------- | ------ | -------------------------------------------------- | ------------------ |
| `github.com`    | GitHub    | `gh`   | `command -v gh`                                    | `gh auth status`   |
| `gitlab.*`      | GitLab    | `glab` | `command -v glab`                                  | `glab auth status` |
| `bitbucket.org` | Bitbucket | `bb`   | `command -v bb` (or other installed Bitbucket CLI) | per-CLI            |

If the CLI is installed and logged in → use the **CLI** for all next steps.

If the CLI is installed but **not logged in**, tell the user how to log in (e.g. `gh auth login`, `glab auth login`). Or offer Tier 3.

## Tier 3 — Claude browser control

If there is no MCP and no working CLI, check if a Claude browser tool is available:

- Claude in Chrome (`mcp__claude-in-chrome__*` tools)
- The built-in browser in the Claude desktop app (`mcp__Claude_Browser__*` tools)

If there is one → use the **browser** for all next steps. Follow these rules each time you use it:

- Work in a **new tab**. Get `<owner>/<repo>` from the remote URL.
- If the page asks to log in, stop. Ask the user to log in, then go on. Never type a password or token yourself.
- Click only the buttons the step needs. Never click merge, close, approve, or delete.
- If a page does not load, or an action fails 2–3 times, stop. Tell the user what went wrong.

PR page URLs:

| Platform  | PR page                                                             |
| --------- | ------------------------------------------------------------------- |
| GitHub    | `https://github.com/<owner>/<repo>/pull/<number>`                   |
| GitLab    | `https://<gitlab-host>/<group>/<project>/-/merge_requests/<number>` |
| Bitbucket | `https://bitbucket.org/<workspace>/<repo>/pull-requests/<number>`   |

## None available

If there is no MCP, no CLI, and no browser tool → tell the user:

> "To read and resolve PR comments, this skill needs an MCP, a platform CLI (`gh`, `glab`, or a Bitbucket CLI), or a Claude browser tool. I could not find one. Please set one up and try again."

Then **end the session**.
