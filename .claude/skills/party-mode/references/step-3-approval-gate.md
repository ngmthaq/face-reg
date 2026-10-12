# Step 3 — User Approval Gate

Before any coding starts, the Root Agent **MUST** show the full plan to the user **as a chat message**. Use the plan template from [Step 2 — Planning](./step-2-planning.md). Then **wait** for clear approval. At this point the plan is only in the chat. It is **not** in any file yet. **DO NOT** make things up.

## Approved

Only **after** the user approves, save the plan to the **Doc Directory** as a Markdown file. This is the first and only time the plan is written to disk. Copy the plan word for word from the chat message. **DO NOT** make things up.

- File name format: `<yyyy-mm-dd-hh-mm-ss>-<plan-name>.md`
- Example: `2026-12-01-16-30-01-handle-send-registration-mail.md`

Then go to **Step 4**.

## Requests Changes

Go back to **Step 1 (Brainstorming)** with the user's change request. Clear up the details again and write a new plan. **DO NOT** start coding sub-agents until the user clearly approves a plan. This gate applies to every planning round. This includes new plans made because of incomplete results.

## Cancels / Aborts

Stop the workflow. Tell the user it has stopped.
