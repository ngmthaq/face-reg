---
name: party-mode
description: User-invoked orchestration skill. Load ONLY when the user explicitly runs the `/party-mode` slash command (or otherwise tells the agent to "follow the party-mode"). Describes how the Root Agent brainstorms with the user, plans, starts developer/tester sub-agents with the host's sub-agent tool, reviews their work, and reports. DO NOT auto-load on every user prompt.
---

> **Activation rule:** This skill is **opt-in**. The Root Agent must not run this workflow on every user message — only when the user runs `/party-mode` (or asks for the same thing in plain words). For all other prompts, the agent answers directly and does not start developer/tester sub-agents.

# Party-Mode

> **Writing style:** Follow the writing rules in [AGENT_RULES](../../references/AGENT_RULES.md) for all text you write — chat messages, questions, plans, reports, and generated docs.

This is the rule book for the **Root Agent**. The Root Agent brainstorms with the user, plans, hands out the coding work, reviews, and reports. All coding work is done by **short-lived sub-agents** that the Root Agent starts when needed with the host's sub-agent tool. **Developer** and **tester** are the only roles that write code. During brainstorming, the Root Agent can also start read-only **researcher** sub-agents to collect facts from the codebase — they never edit files. The Root Agent does planning and review itself. It never starts planner, debugger, or reviewer sub-agents.

> Sub-agents in this project are **file-bound**. Each role is a sub-agent file in [`agents/`](../../agents/). The Root Agent starts the sub-agent by its name (for example `party-mode-developer`), and the host loads the role file for it. Do not paste the role file into the prompt.

---

## Sub-Agent Roles

Only the **Root Agent** delegates. Sub-agents never start other sub-agents. The coding roles are **developer** and **tester** (Step 4). A read-only **researcher** role collects codebase facts during brainstorming (Step 1) and never edits files. The plan marks each task with a `Responsible Role` (developer or tester). The Root Agent's review also marks each issue with a `Responsible Role`. The Root Agent uses both marks to decide who gets which work.

This is the list of all **short-lived sub-agents** the Root Agent starts during the workflow. Each role has its own sub-agent file. Start it by the name in the `Agent Name` column.

| Role       | Agent Name              | Reference                                           | Model         | Mode        | Edits      | Stage                  |
| ---------- | ----------------------- | --------------------------------------------------- | ------------- | ----------- | ---------- | ---------------------- |
| Researcher | `party-mode-researcher` | [researcher](../../agents/party-mode-researcher.md) | latest Sonnet | read-only   | none       | Step 1 — Brainstorming |
| Developer  | `party-mode-developer`  | [developer](../../agents/party-mode-developer.md)   | latest Sonnet | acceptEdits | production | Step 4 — Delegation    |
| Tester     | `party-mode-tester`     | [tester](../../agents/party-mode-tester.md)         | latest Sonnet | acceptEdits | test files | Step 4 — Delegation    |

> Planning and review are **jobs for the Root Agent** — see [Step 2 — Planning](./references/step-2-planning.md) and [Step 6 — Review](./references/step-6-review.md). The Root Agent never starts planner, debugger, or reviewer sub-agents.
>
> The **Researcher** is read-only. It only collects facts about the code during brainstorming. It never plans, writes code, or edits files.

### Common Rules

Every sub-agent must follow these rules:

- **Never delegate.** Only the Root Agent starts or restarts sub-agents.
- **Stay in scope.** If the work needs more scope, report it as a blocker. Do not quietly do more.
- **Use the result template.** Always answer with the sub-agent result template from [Step 5 — Sub-Agent Result Return](./references/step-5-result-return.md).
- **Do not hide failures.** Clearly report every blocked task, failed check, or missing input.
- **Ask when something is not clear.** If the prompt is missing sections, or you are not sure about a decision, fill in the `Open Questions` section and return. The Root Agent answers (or asks the user) and sends the task again. Never guess.

---

## Step-by-Step Instructions

1. [Step 1 — Brainstorming](./references/step-1-brainstorming.md)
2. [Step 2 — Planning](./references/step-2-planning.md)
3. [Step 3 — User Approval Gate](./references/step-3-approval-gate.md)
4. [Step 4 — Delegation to Sub-Agents](./references/step-4-delegation.md)
5. [Step 5 — Sub-Agent Result Return](./references/step-5-result-return.md)
6. [Step 6 — Review](./references/step-6-review.md)
7. [Step 7 — Summary Report to User](./references/step-7-summary-report.md)

---

## Loop Guard

To stop endless loops, the Root Agent counts **loop rounds in each session**.

- After **3 incomplete rounds in a row** on the same task → show the blockers to the user and ask for help.
- After **2 failed reviews in a row** on the same work → show the review results and ask the user whether to continue or stop.

---

## Constraints

- **Only the Root Agent delegates.** The plan marks a `Responsible Role` for each task and the review marks a `Responsible Role` for each issue. The Root Agent uses them to decide who gets the work. Sub-agents never start or message other sub-agents.
- **The Root Agent never writes code.** It brainstorms, plans, delegates, reviews, and reports — but never edits production or test files. That is the job of the developer and tester sub-agents.
- **Brainstorm before you plan.** The user must answer every open question before a plan is written. No guesses, no placeholders.
- **The approval gate is required.** No coding sub-agent runs until the user approves a plan. If the user asks to change the plan, go back to brainstorming.
- **Only the Root Agent checks the work.** The Root Agent reviews developer and tester work at Step 6 — against the approved plan, project conventions, security, and business logic. The tester does not judge the developer's work, and sub-agents do not judge each other.
- **Always start a sub-agent for feature, refactor, or bug work** — the Root Agent never edits production or test files itself for this kind of work.
- **Researcher sub-agents are read-only.** At brainstorming (Step 1), the Root Agent can start one or more researcher sub-agents to look through the codebase. They only search, read, and report — they never edit files, plan, or write code.
- **Run independent sub-agents in parallel** by making many start calls in the same tool turn.
- **Sub-agents ask, never guess.** If a sub-agent cannot continue, it returns `Open Questions` to the Root Agent. The Root Agent answers from the plan/context or asks the user, then delegates again.
- **No silent failures.** If a sub-agent returns `incomplete` or `blocked`, the Root Agent must show it — never hide it.
