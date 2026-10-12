# Phase 1 — Fetch & Analyze the Epic

## 1a. Find the input source

| Source                           | Action                       |
| -------------------------------- | ---------------------------- |
| User pasted text                 | Use it directly              |
| Jira ticket ID (e.g. `PROJ-123`) | Fetch via Atlassian Rovo MCP |
| Linear ticket ID/URL             | Fetch via Linear MCP         |
| GitHub Issue URL or `#number`    | Fetch via GitHub MCP         |

If the user gives a ticket ID but not the system, ask: _"Is that a Jira, Linear, or GitHub issue?"_

**If the MCP is not connected**, try these in order:

1. **CLI** — for GitHub, use `gh issue view <number-or-url>` if `gh` is installed and logged in.
2. **Claude browser control** — if a Claude browser tool is available (Claude in Chrome or the built-in browser in the Claude desktop app), open the ticket in a **new tab** and read the page as text. If you only have a ticket ID, ask the user for the full URL. If the page asks to log in, stop. Ask the user to log in. Never type a password yourself.
3. **Paste** — if nothing works, ask the user to paste the ticket text.

If the input is one feature, not an epic, tell the user. Ask: _"This looks like one feature, not an epic. Should I write one PRD for it, and not split it into many features?"_

## 1b. Ask clarifying questions first

Before you analyze, check if the input answers all of these questions. If not, **ask the user**. Do not make up answers:

- Who are the users (personas)?
- What problem or business need does this epic solve?
- What result or metric should get better?
- Are there known limits (compliance, platform, launch date, existing product areas)?
- Is anything clearly out of scope?

## 1c. Analyze and write a structured summary

Show this summary. Then ask for approval before Phase 2:

```md
## 📋 Epic Analysis

**Title:** <epic title>
**Source:** Jira / Linear / GitHub / Pasted text
**Type:** Epic / User Story / Feature request

### Problem

<3–5 sentences: the user problem or business need this epic solves>

### Desired Outcome

<what success looks like, and which metrics should get better>

### Target Users / Personas

<who this is for, and what each persona wants to do>

### Product Scope

<bullet list of what is in scope. Write it as value for users, not as technical layers>

### Out of Scope / Assumptions

<bullet list of assumptions, and things clearly left out>

### Constraints

<known non-functional limits: performance, security, accessibility, data privacy, compliance, platform>

### Risks / Open Questions

<anything unclear that the team must answer>
```

Then ask: _"Is this analysis correct? Anything to fix before I split the epic into features?"_
