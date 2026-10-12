# Phase 3 — Generate a PRD per Feature

Write one PRD markdown file **for each feature** approved in Phase 2. Also write **one overview file** that lists every PRD. It lets you track the whole epic in one place.

The PRD is the one source of truth for the engineering team. Later, the team writes a technical spec from it.

## File path

Write all files straight into the **Doc Directory** (see `references/PROJECT_OVERVIEW.md`, default `/docs`). Do not use sub-folders:

```
<Doc Directory>/yyyy-mm-dd-<summary>-prd.md
```

- `yyyy-mm-dd` = the date you write the PRD (e.g. `2026-08-07`)
- `<summary>` = the feature name in kebab-case (max 6 words, lowercase, no special characters)

**Example:** `/docs/2026-08-07-self-serve-assessment-creation-prd.md`

## PRD template

```markdown
# <Feature Name>

## Epic

- **Epic PRD:** <link or path to the parent epic document, or the ticket ID/URL>
- **Epic Architecture:** <link or path if one exists, otherwise `N/A`>

## Goal

**Problem:** <3–5 sentences about the user problem or business need this feature solves>

**Solution:** <how this feature solves that problem>

**Impact:** <results or metrics that should get better, e.g. user engagement, conversion rate, time-to-complete>

## User Personas

<the users of this feature, and what each one wants to do>

## User Stories

- As a `<user persona>`, I want to `<perform an action>` so that I can `<achieve a benefit>`.
- ...

<cover the main paths and the edge cases>

## Requirements

### Functional Requirements

- <what the system must do. Clear behavior that you can see>
- ...

### Non-Functional Requirements

- <limits and quality needs: performance, security, accessibility, data privacy>
- ...

## Acceptance Criteria

### <User story or requirement it covers>

- [ ] Given <context>, when <action>, then <visible result>
- [ ] ...

### <Next user story or requirement>

- [ ] ...

## Out of Scope

- <what is clearly not included in this feature>
- ...
```

## Overview file

After the PRDs, write **one** overview file. It links to all of them:

```
<Doc Directory>/yyyy-mm-dd-<epic-summary>-prd-overview.md
```

- `<epic-summary>` = the **epic** name in kebab-case (max 6 words)
- Use the same date and the same Doc Directory as the PRDs. Then links are simple paths in the same folder (`./<file>.md`)

**Example:** `/docs/2026-08-07-performance-review-cycle-prd-overview.md`

### Overview template

```markdown
# <Epic Name> — PRD Overview

- **Epic:** <ticket ID / URL, or `N/A`>
- **Created:** yyyy-mm-dd
- **Features:** <n> · **Done:** <n> · **In progress:** <n> · **Not started:** <n>

## Summary

<2–4 sentences: what this epic gives, and to whom>

## Feature PRDs

| #   | Feature                        | PRD                                                       | Personas            | Depends On | Ticket | Status         |
| --- | ------------------------------ | --------------------------------------------------------- | ------------------- | ---------- | ------ | -------------- |
| 1   | Self-serve assessment creation | [PRD](./2026-08-07-self-serve-assessment-creation-prd.md) | Team Manager        | —          | —      | ⬜ Not started |
| 2   | Assessment results dashboard   | [PRD](./2026-08-07-assessment-results-dashboard-prd.md)   | Team Manager, Admin | #1         | —      | ⬜ Not started |

**Status legend:** ⬜ Not started · 🚧 In progress · ✅ Done

## Delivery Order

<the order to build the features, based on the Depends On column. Say what can be built at the same time>

1. #1 Self-serve assessment creation
2. #2 Assessment results dashboard _(blocked by #1)_

## Deferred to a later epic

- <features raised in Phase 2 but clearly not part of this epic>

## Open Questions

- [ ] <unclear point from Phase 1 or 2 that is still open, and who must answer it>
```

### Overview rules

- **Rows match Phase 2 exactly.** Same numbers, same feature names, same dependencies. If a feature was split or merged after Phase 2, change the numbers here and in the PRDs.
- **Every feature has a row.** You cannot track a PRD with no link.
- **Ticket column starts as `—`.** Phase 4 fills it in after it creates the tickets.
- **Status starts as ⬜ Not started** for every feature. After that, people update it by hand.
- **Always keep Open Questions.** If there are none, write `- None`.

## Rules

- **One file per feature.** Do not put several features in one PRD.
- **One overview file per epic.** Write it again when features are added, split, or removed.
- **No coding details.** No schemas, endpoints, libraries, file names, or architecture. If a requirement sounds technical, rewrite it as behavior you can see.
- **Every user story has acceptance criteria.** A story with no AC is not done.
- **Out of Scope is never empty.** If nothing is left out, say so. Also say where this feature ends and the next features begin.
- If there is a dependency, link to the other feature by its PRD path.

## After writing

Show a summary of the files you wrote:

```markdown
## 📄 PRDs Generated

| #   | Feature                        | Path                                                   |
| --- | ------------------------------ | ------------------------------------------------------ |
| 1   | Self-serve assessment creation | /docs/2026-08-07-self-serve-assessment-creation-prd.md |
| 2   | Assessment results dashboard   | /docs/2026-08-07-assessment-results-dashboard-prd.md   |

**Overview:** /docs/2026-08-07-performance-review-cycle-prd-overview.md
```

Then ask: _"PRDs saved ✅. You can track them in the overview file. Should I now create the feature tickets in your ticket system?"_
