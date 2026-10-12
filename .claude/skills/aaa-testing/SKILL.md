---
name: aaa-testing
description: "AAA (Arrange-Act-Assert) — Makes tests follow the Arrange-Act-Assert pattern so they are clear, well structured, and easy to maintain. Use when writing, reviewing, or refactoring any unit or integration tests that are hard to read, mix setup with assertions, have an unclear goal, or do not follow one structure. Applies to any language and any testing framework (Jest, PyTest, JUnit, RSpec, Go testing, etc.)."
---

# AAA — Arrange, Act, Assert

> **Writing style:** Follow the writing rules in [AGENT_RULES](../../references/AGENT_RULES.md) for all text you write — chat messages, questions, plans, reports, and generated docs.

## The Pattern

Every test has exactly three parts (phases):

| Phase       | Question                              | What belongs here                            |
| ----------- | ------------------------------------- | -------------------------------------------- |
| **Arrange** | What is the world before this action? | Object creation, mocks, test data            |
| **Act**     | What is being tested?                 | The single method call or event under test   |
| **Assert**  | Did it do the right thing?            | Checks on return values, state, side effects |

```javascript
it("applies 10% discount when order exceeds $100", () => {
  // Arrange
  const cart = new Cart();
  cart.add({ name: "Widget", price: 60 });
  cart.add({ name: "Gadget", price: 50 });

  // Act
  const total = cart.calculateTotal();

  // Assert
  expect(total).toBe(99); // 110 - 10% discount
});
```

## Common Violations

**1. Phases are not split — many acts/asserts are packed into one test.**
Write one test per behavior. When a test fails, you must know exactly what broke.

**2. Assertions in Arrange.** Trust your fixtures (shared test setup). If you need to check fixture state, write a separate test for it.

**3. Act hidden in Arrange.** The thing you test must be on its own line in the Act phase.

```python
# Bad — register() is the Act, hidden in Arrange
user = UserService(mailer=mailer).register(payload)

# Good
service = UserService(mailer=mailer)   # Arrange
service.register(payload)              # Act
```

**4. Asserting too much.** Assert only what the test is _about_. Extra assertions make tests break easily and make failure messages confusing.

## Shared Arrange

Move repeated setup into `beforeEach`/fixtures, but keep Act and Assert inside each test:

```javascript
describe("Cart", () => {
  let cart;
  beforeEach(() => {
    cart = new Cart();
    cart.add({ name: "Widget", price: 10 });
  });

  it("calculates correct total", () => {
    const total = cart.calculateTotal(); // Act
    expect(total).toBe(10); // Assert
  });

  it("applies coupon discount", () => {
    cart.applyCoupon("SAVE10"); // Act
    expect(cart.calculateTotal()).toBe(9); // Assert
  });
});
```

## Test Naming

Name tests after behavior: **`[unit]_[scenario]_[expected outcome]`** or plain prose.

| Bad          | Good                                            |
| ------------ | ----------------------------------------------- |
| `test_login` | `returns auth token when credentials are valid` |
| `test_error` | `throws ValidationError when email is missing`  |

## Rules

1. **All three phases must be present** — no Act = the test checks nothing; no Assert = the test can never fail.
2. **One Act per test** — two method calls under test means two tests.
3. **No assertions in Arrange** — check that fixtures are correct in a separate test.
4. **Assert only what the test is about** — leave out checks on unrelated fields.
5. **Name tests after behavior**, not after how the code works inside.
6. **Shared setup in `beforeEach`/fixtures** — never repeat Arrange, but keep Act+Assert per test.
7. **In code review**, flag as: "AAA violation: [phase] is [missing/mixed/bloated]."
