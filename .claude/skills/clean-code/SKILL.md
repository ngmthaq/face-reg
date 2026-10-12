---
name: clean-code
description: "Clean Code — One reference for all clean code principles: SOLID, DRY, KISS, Separation of Concerns, and Atomic Design. Grouped by type of work: OOP, Functional, UI/Component, Backend/API, and Code Review. Use when writing, reviewing, or refactoring code in any language or paradigm."
---

# Clean Code

> **Writing style:** Follow the writing rules in [AGENT_RULES](../../references/AGENT_RULES.md) for all text you write — chat messages, questions, plans, reports, and generated docs.

Use this skill when writing, reviewing, or refactoring code. The detailed patterns live in the `references/` folder. This keeps the main skill short and lets you reuse each guide.

## How to Use This Skill

1. Find the type of work (context) in the table below.
2. Load the linked references in the listed order.
3. Use more than one reference when the task covers many layers or coding styles.
4. For reviews, apply the matching references first, then run the checklist.

---

## Five contexts and their load order

| Context                      | Apply in order                                                          |
| ---------------------------- | ----------------------------------------------------------------------- |
| OOP Languages                | SOLID → Separation of Concerns → DRY                                    |
| Functional / General-Purpose | Separation of Concerns → DRY → KISS                                     |
| UI / Component Development   | Atomic Design → Separation of Concerns → DRY → KISS                     |
| Backend / API                | SOLID → Separation of Concerns → DRY → KISS                             |
| Code Review                  | SOLID + DRY + KISS + Separation of Concerns + Atomic Design + Checklist |

---

## Reference Index

- [SOLID](./references/solid.md)
- [DRY](./references/dry.md)
- [KISS](./references/kiss.md)
- [Atomic Design](./references/atomic-design.md)
- [Separation of Concerns](./references/separation-of-concerns.md)
- [Code Review Checklist](./references/code-review-checklist.md)

---

## Universal Rules

These rules always apply, in every context and principle:

1. **Name things after what they do.** If a name needs "and" or "or", the thing does too much.
2. **Test business logic on its own.** It must not need a DB, HTTP, or a UI framework.
3. **Flag violations by principle name** in reviews: "SRP violation", "DRY violation", "KISS violation", etc.
4. **Don't abstract too early.** Only extract shared code after the same code shows up at least twice.
5. **Cross-cutting concerns** (logic used in many places, like auth, logging, validation) belong in middleware/decorators — never inline.
