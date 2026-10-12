# Separation of Concerns

Keep business logic out of components. The UI only shows things. The domain logic makes decisions.

```javascript
// Bad — business rules inside a React component
function CheckoutPage({ cart }) {
  const tax = cart.total * 0.08;
  const discount = cart.items.length > 5 ? cart.total * 0.1 : 0;
  const finalPrice = cart.total + tax - discount;
  return <div>Total: {finalPrice}</div>;
}

// Good — domain logic moved out, UI only shows the result
function calculateOrderTotal(cart) {
  const tax = cart.total * TAX_RATE;
  const discount = cart.items.length > 5 ? cart.total * DISCOUNT_RATE : 0;
  return cart.total + tax - discount;
}

function CheckoutPage({ cart }) {
  const total = calculateOrderTotal(cart);
  return <div>Total: {total}</div>;
}
```

Split the system into layers. Each layer has one job.

```python
# Bad — data access, business logic, and side effects all in one function
def process_refund(order_id):
    order = db.query("SELECT * FROM orders WHERE id = ?", order_id)
    if order.status != 'completed':
        raise ValueError("Only completed orders can be refunded")
    if (datetime.now() - order.created_at).days > 30:
        raise ValueError("Refund window expired")
    db.execute("UPDATE orders SET status='refunded'...")
    stripe.refund(order.payment_id)
    email.send(order.customer_email, "Refund processing")

# Good — each layer does its own job
class OrderRepository:
    def find(self, order_id): ...
    def update_status(self, order_id, status): ...

class RefundService:
    def __init__(self, order_repo, payment_gateway, notifier): ...
    def process_refund(self, order_id):
        order = self.order_repo.find(order_id)
        self._validate_eligibility(order)            # business rules only
        self.payment_gateway.refund(order.payment_id)
        self.order_repo.update_status(order_id, 'refunded')
        self.notifier.send_refund_confirmation(order)
```

```typescript
// Bad — cross-cutting concerns inline
async function createUser(data: UserInput) {
  if (!currentUser.hasPermission("create_user")) throw new ForbiddenError();
  if (!data.email.includes("@")) throw new ValidationError("Invalid email");
  logger.info(`Creating user: ${data.email}`);
  const user = new User(data);
  await userRepo.save(user);
  logger.info(`User created: ${user.id}`);
  return user;
}

// Good — cross-cutting handled by decorators
@RequirePermission("create_user")
@ValidateInput(CreateUserSchema)
@LogOperation("createUser")
async function createUser(data: UserInput) {
  const user = new User(data);
  await userRepo.save(user);
  return user;
}
```

## SoC Rules

1. You must be able to test business logic by itself, with no DB, no HTTP, and no UI framework.
2. Controllers must be small: check input → call domain logic → return output. No business rules.
3. Repositories must be simple. They only convert between domain objects and storage.
4. Cross-cutting concerns (things used everywhere, like auth, logging, and validation) go in middleware or decorators. Do not put them inside business functions.
5. Ask: "What would make this code change?" If there are many unrelated reasons, the jobs are mixed.
6. Point it out with: "SoC violation: this function handles both `[concern A]` and `[concern B]`."
