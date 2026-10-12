# Step 4 — Delegation to Sub-Agents

The Root Agent reads the approved plan. Then it starts the right sub-agents. There are only two sub-agent roles here: **developer** and **tester**. Each one has its own sub-agent file. Start it by its name (see [Sub-Agent Roles](../SKILL.md#sub-agent-roles)).

> **ALWAYS** start a sub-agent. **DO NOT** change code yourself.
> Start both sub-agents on the latest **Sonnet** model, not Opus or Fable. This uses fewer tokens.

## Start the developer sub-agent

Use this for coding tasks from the approved plan. Start the `party-mode-developer` sub-agent. The host loads its role file, so do not paste it into the prompt.

> Prompt template: [developer → Delegation Prompt Template](../../../agents/party-mode-developer.md#delegation-prompt-template)
> Sub-agent: `party-mode-developer` — [party-mode-developer](../../../agents/party-mode-developer.md)

## Start the tester sub-agent

Use this for test tasks from the approved plan. Start the `party-mode-tester` sub-agent. The host loads its role file, so do not paste it into the prompt.

> Prompt template: [tester → Delegation Prompt Template](../../../agents/party-mode-tester.md#delegation-prompt-template)
> Sub-agent: `party-mode-tester` — [party-mode-tester](../../../agents/party-mode-tester.md)

## Running in parallel

Sometimes the developer and tester work do not overlap, or the project's `Testing Workflow` is `Test-First`. Then the Root Agent **must** start both sub-agents in the **same tool turn** (many tool calls in one message). This way they run at the same time.

In all other cases, start them one by one: developer first, then tester.

## Re-delegation

If the review in Step 6 finds problems, start the sub-agent again. Use the role named in each issue's `Responsible Role` (`developer` → `party-mode-developer`, `tester` → `party-mode-tester`). Paste the review feedback into the `Review Feedback` section of the new prompt.
