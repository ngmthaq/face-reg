# Phase 4 — Create Feature Tickets

Create **one ticket per feature**, not one per coding task. The engineering team splits each feature ticket into technical tasks later, based on the PRD.

## 4a. Choose where to create the tickets

Ask the user (if they did not say yet):

> "Where should I create these feature tickets?"
>
> - Jira (as child issues under the epic)
> - Linear (as sub-issues under the parent)
> - GitHub Issues (in a repo)

When the user picks a system, confirm where: project key, team, or repo.

## 4b. Create tickets

**For each feature**, create a ticket with the matching MCP. Use this content:

- **Title:** feature name from Phase 2
- **Description:**
  - Goal: problem, solution, impact (from the PRD)
  - User stories
  - Acceptance criteria, as a checklist
  - Out of scope
  - Link/path to the full PRD file
- **Labels/Tags:** `feature` (or `enabler`), and the product area if you know it. Do **not** add layer tags like `frontend`, `api`, or `db`.
- **Linked to parent:** link the ticket to the original epic.
- **Dependencies:** add "blocked by" links for the product dependencies in the Phase 2 table.

Create tickets **in dependency order**. Then each "blocked by" link points to a ticket that already exists.

## 4c. Update the PRD overview

Edit the overview file from Phase 3 (`<Doc Directory>/yyyy-mm-dd-<epic-summary>-prd-overview.md`). In every row, fill in the **Ticket** column with the new ticket ID and its link, e.g. `[PROJ-124](<url>)`. Leave Status as ⬜ Not started. The team updates it.

## 4d. Show a summary

When all tickets are created, show a summary table:

```markdown
## ✅ Feature Tickets Created

| #   | Ticket ID | Feature                        | PRD                                                    | Link  |
| --- | --------- | ------------------------------ | ------------------------------------------------------ | ----- |
| 1   | PROJ-124  | Self-serve assessment creation | /docs/2026-08-07-self-serve-assessment-creation-prd.md | <url> |
| 2   | PROJ-125  | Assessment results dashboard   | /docs/2026-08-07-assessment-results-dashboard-prd.md   | <url> |

**Parent epic:** PROJ-123 — features linked ✅
**Overview updated:** /docs/2026-08-07-performance-review-cycle-prd-overview.md
```

## MCP Reference

| System | MCP to use         | Notes                                                               |
| ------ | ------------------ | ------------------------------------------------------------------- |
| Jira   | Atlassian Rovo MCP | Use it to read and create. Link features to the epic with Epic Link |
| Linear | Linear MCP         | Use sub-issues under the parent. Set the project if there is one    |
| GitHub | GitHub MCP         | Create issues with labels. Use a milestone or project board if any  |

## No MCP — use the browser

If the MCP is not connected, check if a Claude browser tool is available (Claude in Chrome or the built-in browser in the Claude desktop app). If there is one:

1. Tell the user you will create the tickets in the browser, and wait for a "yes".
2. Open the project in a **new tab**. If the page asks to log in, stop. Ask the user to log in. Never type a password yourself.
3. For each feature, in dependency order, open the "new ticket" form. For GitHub: `https://github.com/<owner>/<repo>/issues/new`. For Jira and Linear, use the **Create** button.
4. Fill in the title, description, labels, and parent link from 4b. Then click the create button. Do not click any other button that changes things.
5. Save the new ticket ID and URL from the page.
6. If a field cannot be set in the form (e.g. a "blocked by" link), list it in the summary so the user can set it by hand.

If a page does not load, or an action fails 2–3 times, stop. Tell the user what went wrong.

If there is no MCP and no browser tool, tell the user: _"[Jira/Linear/GitHub] is not connected. You can turn it on in the tools menu."_
