# SOLID

## S — Single Responsibility Principle

Each class, module, or function has **only one reason to change**.

```javascript
// Bad — validates, saves, emails, and logs in one class
class UserService {
  createUser(data) {
    /* validates + saves to DB + sends email + logs audit */
  }
}

// Good — each class has one job
class UserValidator {
  validate(data) {
    ...
  }
}
class UserRepository {
  save(user) {
    ...
  }
}
class UserNotifier {
  sendWelcomeEmail(user) {
    ...
  }
}
class UserService {
  constructor(validator, repository, notifier) {
    ...
  }
  createUser(data) {
    /* calls the classes above in order */
  }
}
```

## O — Open/Closed Principle

Open to new behavior, closed to changes. Add new behavior without changing old code.

```javascript
// Bad — must edit this function for every new discount type
function calculateDiscount(type) {
  if (type === "student") return 0.2;
  if (type === "senior") return 0.3;
}

// Good — new discount = new class, no existing code touched
interface DiscountStrategy {
  calculate(): number;
}
class StudentDiscount implements DiscountStrategy {
  calculate() {
    return 0.2;
  }
}
class SeniorDiscount implements DiscountStrategy {
  calculate() {
    return 0.3;
  }
}
```

## L — Liskov Substitution Principle

A subtype must work in every place its base type works. Nothing should break.

```javascript
// Bad — Penguin breaks what Bird promises
class Bird {
  fly() {
    ...
  }
}
class Penguin extends Bird {
  fly() {
    throw new Error("Cannot fly");
  }
}

// Good — change the class tree to match real life
class Bird {
  move() {
    ...
  }
}
class FlyingBird extends Bird {
  fly() {
    ...
  }
}
class Penguin extends Bird {
  swim() {
    ...
  }
}
```

## I — Interface Segregation Principle

Code should not have to depend on methods it does not use.

```javascript
// Bad — Robot must implement eat() and sleep()
interface Worker {
  work(): void;
  eat(): void;
  sleep(): void;
}

// Good — split into small interfaces
interface Workable {
  work(): void;
}
interface Feedable {
  eat(): void;
}
interface Restable {
  sleep(): void;
}
// Robot implements only Workable
```

## D — Dependency Inversion Principle

High-level modules depend on abstractions (interfaces), not on concrete classes.

```javascript
// Bad — tightly coupled to MySQL and SMTP
class OrderService {
  private db = new MySQLDatabase();
  private mailer = new SmtpMailer();
}

// Good — depends on interfaces, passed in from outside
class OrderService {
  constructor(
    private db: Database,
    private mailer: Mailer,
  ) {}
}
```

## SOLID Rules

1. Before you write a class, find its one job. Name the class after that job.
2. Before you add a new `if` branch for a new type, think about an interface and a new class instead.
3. Before you merge, check that every subtype can safely replace its base type.
4. Ask: "Will every class that implements this use every method?" If not, split the interface.
5. High-level modules must use interfaces, not concrete classes.
6. Name the principle when you point out a problem: "SRP violation: this class handles both X and Y."
