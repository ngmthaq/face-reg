# Phase 2 — Feature Breakdown

Split the epic into **features and enablers**. These are parts of the product scope. Each part gives value on its own. Each part gets its own PRD in Phase 3.

## What counts as a feature

- You can write it as a user story: _"As a `<persona>`, I want to `<action>` so that I can `<benefit>`."_
- It gives clear value to a user or to the business on its own.
- You can check it with acceptance criteria. You do not need to talk about how the code works.
- An **enabler** (e.g. "Tenant-level audit log retention policy") is OK when it makes user value possible later. Say which features it helps.

## What is NOT a feature — do not write these

- Technical layers or components: `[DB] Add table`, `[API] Add endpoint`, `[FRONTEND] Build form`
- Coding steps: "write migration", "add validation", "connect state management"
- Test tasks, refactors, or code-review tasks
- Effort estimates, story points, or sizes in days
- Any technical order of work (schema → API → UI)

If a title starts with a layer tag, it is dev work. Merge it back into its feature.

## Output format

Show a Markdown table:

```markdown
## 🔨 Feature Breakdown

| #   | Feature Name                   | Problem / User Value                                                   | Primary Personas    | Depends On |
| --- | ------------------------------ | ---------------------------------------------------------------------- | ------------------- | ---------- |
| 1   | Self-serve assessment creation | Managers cannot start an assessment without ops help, delaying reviews | Team Manager        | —          |
| 2   | Assessment results dashboard   | Managers have no view of completion or scores across their team        | Team Manager, Admin | #1         |
| ... |                                |                                                                        |                     |            |
```

After the table, add:

```markdown
### Deferred to a later epic

<features that came up but are clearly not part of this epic>
```

## Dependencies

Here, a dependency is a **product** dependency. Feature B cannot be used, or has no meaning, until feature A exists. Write it as `#row_number`. If there is none, write `—`.

## How big a feature should be

A feature should be small enough for one PRD. One PRD should not mix unrelated user journeys. A feature should also be big enough to ship on its own and give value.

- If a feature covers two unrelated personas doing two unrelated jobs, split it.
- If a "feature" only makes sense as part of another one, merge them.

After the table, ask: _"Is this feature list correct? Before I write the PRDs, you can ask me to split, merge, reorder, move to later, or change any feature."_
