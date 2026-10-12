# Step 1 — Brainstorming (Root Agent)

When a user prompt comes in, the Root Agent **must first greet the user, classify the request, and brainstorm the requirement with the user**. Brainstorming is a two-way talk. The Root Agent makes the goal clear, classifies the request, looks at the related code, and lists every open question. All this happens **before** any plan is written.

> The Root Agent runs brainstorming itself. If the search is big or covers many files, it can start one or more **read-only researcher sub-agents** (`party-mode-researcher`) to search the codebase. These sub-agents only research and report. They never edit files. No developer or tester (coding) sub-agent starts at this stage.

---

## Check Task Complexity

**Before you classify the request, check how big it is.** A task is **big** when it:

- covers many layers (DB / API / business logic / UI),
- is an epic, user story, or feature request that is too big for a few small tasks, or
- has many independent parts.

**If the task is big, STOP.** Tell the user to run the [ticket-breakdown](../../ticket-breakdown/SKILL.md) skill first. That skill splits the work into feature tickets, each with its own PRD. Then **end the session**. Do not classify, brainstorm more, plan, or start any sub-agent. After the breakdown, the user runs `/party-mode` again on one feature ticket.

Go on to classification only when the task is small enough to handle directly.

---

## Classify the Intent

The class decides which questions you ask in brainstorming, and how the plan looks.

### Feature

Use `feature` when the prompt asks for:

- New functionality
- New or changed agent skills that add new abilities
- A refactor or an improvement of existing behaviour
- A speed improvement when nothing is broken
- A safe change that adds value or makes the user experience better
- A change the user clearly calls a "feature"

**Signal words:** "add", "implement", "create", "build", "refactor", "improve", "migrate", "support", "enable", "integrate"

### Bug

Use `bug` when the prompt describes:

- Something that worked before and is now broken
- Unexpected or wrong behaviour
- A crash, error, or exception
- A regression (a recent change broke something)
- Output that does not match the spec
- A change the user clearly calls a "bug"

**Signal words:** "broken", "not working", "fails", "error", "crash", "wrong", "incorrect", "regression", "unexpected", "should be", "used to work"

### Unclear Cases

**Rule: ALWAYS ask the user. Never guess.**

If the prompt has signs of both `feature` and `bug`, or you are not sure, ask the user a direct, specific question before you go on. Do not go on with your best guess.

---

## Brainstorming Dialogue

1. **Greet the user and repeat the request** in your own words. This shows any misunderstanding right away. User prompts can be confusing or have spelling errors. Read them carefully and make them clear.
2. **Check task complexity** (see [Check Task Complexity](#check-task-complexity) above). If the task is big, tell the user to run the [ticket-breakdown](../../ticket-breakdown/SKILL.md) skill first. Then **end the session**. Do not go on to classification.
3. **Classify the intent** (`feature` or `bug`) with the rules above.
4. **Look at the codebase.** Read the related files, modules, and conventions (read-only). Use real paths. Do not make up files.
   - If the search is big, covers many files, or is faster in parallel, **start one or more read-only researcher sub-agents** (`party-mode-researcher`). They collect the facts and report back.
   - To run independent researchers in parallel, start them all in the same tool turn.
   - Researchers are strictly read-only. They search, read, and sum up. They never edit production or test files.
5. **Load related documents.** Look in the **Documents Folder** for old plans or memory items about this request.
6. **Look in the `skills/` directory.** Note every skill that fits the request. You will give these to sub-agents later.
7. **Collect details for the class:**
   - For a `feature`: scope, expected behaviour, affected areas, limits, and what is clearly out of scope.
   - For a `bug`: what happens now (error messages, stack traces, logs), what should happen, and steps to reproduce. Follow the steps through the code to find the likely root cause.
8. **Show every open question to the user.** Write each unclear point as a direct, specific question: goal, scope, affected area, expected behaviour, limits. **STOP and wait** until the user answers every question. Only then move to planning.
9. **Repeat.** If the answers bring new questions, ask again. Brainstorming ends only when the Root Agent can describe the requirement with nothing left unclear.

---

## Usage Notes

- Brainstorming is always the Root Agent's **first action**. No planning or coding delegation happens before it. Only read-only researcher sub-agents may run at this stage, and only to collect codebase facts.
- **ALWAYS ask the user when anything is unclear.** Never guess.
- The Root Agent also comes back to this step when the user asks for plan changes at the approval gate (Step 3).
- If a request cannot be made clear, treat it as blocked until the user answers. Never go on with placeholders.
