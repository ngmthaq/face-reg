# Code Review Checklist

Use this checklist on any pull request. It works for any language or style.

## SOLID _(OOP)_

- [ ] SRP: Does each class/module have exactly one reason to change?
- [ ] OCP: Are new types added with new code, not by changing old `if`/`switch` blocks?
- [ ] LSP: Do all subtypes keep the promises of the base class?
- [ ] ISP: Are interfaces small? Do classes use every method they implement?
- [ ] DIP: Do high-level modules depend on abstractions, not concrete classes?

## DRY _(All)_

- [ ] No repeated logic, magic numbers, or copy-pasted code
- [ ] Shared types and schemas are in one place
- [ ] Test setup uses factory functions, not the same values again and again

## KISS _(All)_

- [ ] No abstraction added only for maybe-later needs
- [ ] Nesting is 2 levels or less (if not, use guard clauses)
- [ ] No clever one-liners that are hard to understand

## Separation of Concerns _(All)_

- [ ] Business logic does not depend on UI, DB, or HTTP
- [ ] Controllers/handlers are small
- [ ] Auth, logging, and validation are in middleware, not inside the function

## Atomic Design _(UI only)_

- [ ] No data fetching below the Page level
- [ ] No business logic inside components
- [ ] No upside-down levels (molecule importing organism, etc.)
