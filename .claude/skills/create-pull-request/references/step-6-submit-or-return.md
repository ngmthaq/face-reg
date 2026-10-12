# Step 6 — Create the PR

Use the first method that works, in this order:

1. **Platform MCP** — best choice
2. **Platform CLI** — if there is no MCP
3. **Claude browser control** — if there is no MCP and no working CLI
4. **Copy-paste** — last choice

## Tier 1 — Platform MCP

Check if there is an MCP for the platform:

| Platform  | MCP tool                                                    |
| --------- | ----------------------------------------------------------- |
| GitHub    | `github-pull-request_create_pull_request` or any GitHub MCP |
| GitLab    | GitLab MCP (tool to create a merge request)                 |
| Bitbucket | Bitbucket MCP (tool to create a pull request)               |

If there is one:

1. Show the filled template to the user.
2. Ask: _"Should I create this PR now with the [Platform] MCP?"_
3. If yes, call the MCP tool. Use `<target-branch>` and the filled description.
4. Send the PR link to the user.

## Tier 2 — Platform CLI

If there is no MCP, check the CLI for the platform from [Step 1](./step-1-detect-platform.md):

| URL has         | Platform  | CLI    | Is it installed?                           | Is it logged in?   |
| --------------- | --------- | ------ | ------------------------------------------ | ------------------ |
| `github.com`    | GitHub    | `gh`   | `command -v gh`                            | `gh auth status`   |
| `gitlab.*`      | GitLab    | `glab` | `command -v glab`                          | `glab auth status` |
| `bitbucket.org` | Bitbucket | `bb`   | `command -v bb` (or another Bitbucket CLI) | depends on the CLI |

If the CLI is installed and logged in:

1. Show the filled template to the user.
2. Ask: _"Should I create this PR now with `<cli>`?"_
3. If yes, save the description to a temp file. This avoids quote problems with long Markdown. Then run:

   **GitHub**

   ```bash
   gh pr create --base <target-branch> --title "<title>" --body-file <tmpfile>
   ```

   **GitLab**

   ```bash
   glab mr create --target-branch <target-branch> --title "<title>" --description "$(cat <tmpfile>)"
   ```

   **Bitbucket** — each CLI has different flags. For `bb`:

   ```bash
   bb pr create --target <target-branch> --title "<title>" --description "$(cat <tmpfile>)"
   ```

4. Delete the temp file.
5. Send the PR link from the CLI output to the user.

If the CLI is installed but **not logged in**, tell the user how to log in (e.g. `gh auth login`, `glab auth login`). Or offer Tier 3.

## Tier 3 — Claude browser control

Check if a Claude browser tool is available:

- Claude in Chrome (`mcp__claude-in-chrome__*` tools)
- The built-in browser in the Claude desktop app (`mcp__Claude_Browser__*` tools)

If there is none, go to Tier 4.

If there is one:

1. Show the filled template to the user.
2. Ask: _"Should I create this PR now in your browser?"_
3. If yes, check that your branch is on the remote: `git ls-remote --heads origin <current-branch>`. If it is not, ask the user first. Then run `git push -u origin <current-branch>`.
4. Open a **new tab** with the "new PR" page. Get `<owner>/<repo>` from the remote URL in [Step 1](./step-1-detect-platform.md):

   | Platform  | "New PR" page URL                                                                                                                                         |
   | --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
   | GitHub    | `https://github.com/<owner>/<repo>/compare/<target-branch>...<current-branch>?expand=1`                                                                   |
   | GitLab    | `https://<gitlab-host>/<group>/<project>/-/merge_requests/new?merge_request[source_branch]=<current-branch>&merge_request[target_branch]=<target-branch>` |
   | Bitbucket | `https://bitbucket.org/<workspace>/<repo>/pull-requests/new?source=<current-branch>&dest=<target-branch>`                                                 |

5. If the page asks to log in, stop. Ask the user to log in, then go on. Never type a password or token yourself.
6. Check that both branches on the page are correct. Then type the title and description.
7. Click the create button. Do not click any other button that changes things (like merge, close, or delete).
8. Send the PR link to the user.

If the page does not load, or a step fails 2–3 times, stop. Tell the user what went wrong. Then go to Tier 4.

## Tier 4 — Copy-paste

If nothing else works:

- Give the user the filled description in a Markdown code block. The user can copy it into the platform.
