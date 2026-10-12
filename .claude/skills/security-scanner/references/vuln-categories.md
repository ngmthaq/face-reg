# Vulnerability Categories

Tools find syntax problems. This file helps you find logic problems. For each category, follow the flow
`[untrusted source] → [processing] → [dangerous sink]`. Ask: what can an attacker control?

---

## Injection

### SQL Injection (CWE-89)

```js
// ❌ String concat / template literals reach the query — both are unsafe
const q = "SELECT * FROM users WHERE email = '" + req.body.email + "'";
const q = `SELECT * FROM users WHERE id = ${req.params.id}`;

// ✅ Parameterized query — input is data, never SQL
db.execute("SELECT * FROM users WHERE email = ?", [req.body.email]);
User.findOne({ where: { email: req.body.email } }); // ORM bound params
```

**Signs to look for:**

- `.query()`, `.execute()`, `.raw()`, `.exec()` with any `+` or `${}` near user input.
- ORM raw-query helpers (`sequelize.literal`, `Model.objects.extra`,
  `createQueryBuilder().where(...)` with interpolation).
- Dynamic `ORDER BY` or table names. Parameters cannot hold table or column names, so use an allowlist.

**Second-order SQLi:** a value is saved in the DB. Later, it is added into a query as a string. Check
that values read from the DB are not trusted at the sink.

### Cross-Site Scripting — XSS (CWE-79)

```jsx
// ❌ Raw HTML injection — attacker injects <script> or event handlers
<div dangerouslySetInnerHTML={{ __html: userComment }} />;
document.getElementById("out").innerHTML = userInput;

// ✅ Text content only (React escapes by default); sanitize if HTML is required
<div>{userComment}</div>
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userComment) }} />
```

**Signs to look for:** `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`,
`eval`, `new Function`, `$(...).html()`, `v-html`, `dangerouslySetInnerHTML`; unescaped
server-side template output — `{{{ var }}}` (Handlebars), `| safe` / `{% autoescape off %}`
(Jinja2/Django), `<%= raw %>` (ERB), `@Html.Raw` (Razor).

**Also check:** `href={userInput}` and `src={userInput}`, which allow `javascript:` URLs. Also check
user values shown back in error pages.

### Command Injection (CWE-78)

```python
# ❌ User input reaches the shell — attacker appends "; rm -rf /"
os.system(f"convert {filename} output.png")
subprocess.call("convert " + filename, shell=True)

# ✅ Argument list form — no shell interpretation; allowlist input first
if not re.match(r'^[\w\-]+\.pdf$', filename):
    raise ValueError("Invalid filename")
subprocess.run(["convert", filename, "output.png"])
```

**Signs to look for:** `child_process.exec` / `execSync` (Node.js — use `execFile` instead),
`Runtime.getRuntime().exec` with a concatenated string (Java), `shell=True` (Python),
backticks and `system()` (Ruby/PHP), `exec.Command("sh", "-c", ...)` (Go).

### Other Injection Sinks

- **LDAP** — user input in a filter string, with no escaping of `()*\|&`.
- **XPath** — concatenated node expressions.
- **Header / response splitting** — `\r\n` in a redirect target or a `Set-Cookie` value.
- **Log injection** — unescaped newlines in log lines. Attackers can use them to add fake log entries.
- **Template injection (SSTI)** — user input is compiled as a template (`render_template_string`,
  Handlebars `compile`, Thymeleaf expressions). It should be passed as data instead.

---

## Authentication & Access Control

### Broken Authorization / IDOR / BOLA (CWE-284, CWE-639)

```js
// ❌ Authenticated but not authorized — any user can fetch any invoice
app.get("/invoice/:id", authenticate, async (req, res) => {
  res.json(await Invoice.findById(req.params.id));
});

// ✅ Scope the query to the requesting user's ownership
res.json(await Invoice.findOne({ _id: req.params.id, ownerId: req.user.id }));
```

Check that **every** DB lookup by a user-given ID also checks who owns the record. Check
that admin routes have middleware that checks roles. A sensitive route with no
login check at all is CRITICAL, not HIGH.

### JWT Weaknesses

- `algorithms` not set on verify → `alg: none` or HS256/RS256 confusion attack.
- Weak or hardcoded signing secret. The same secret in every environment.
- `exp` not checked, or a token that lasts for months.
- Sensitive claims trusted without checking the signature (`jwt.decode` instead of `jwt.verify`).
- No way to cancel (revoke) stolen tokens.

### CSRF (CWE-352)

```js
// ❌ State-changing endpoint with cookie auth, no origin check
app.post("/transfer", handler);

// ✅ Synchronizer token or SameSite cookie
app.use(csrf());
// Set-Cookie: session=x; SameSite=Strict; Secure; HttpOnly
```

APIs that log in **only** with an `Authorization: Bearer` header are safe from CSRF.
Browsers do not send custom headers to other sites by default. Do not report those.

### Mass Assignment (CWE-915)

Never pass `req.body` straight into a model constructor or `update`. An attacker can add
`isAdmin: true`. List the allowed fields yourself:
`User.create({ name: req.body.name, email: req.body.email })`.

### Session & Privilege

- Session ID not changed after login (session fixation).
- Missing `HttpOnly` / `Secure` / `SameSite` on session cookies.
- Role checked only on the client, or read from a field the user sends.
- Password reset tokens that are easy to guess, last too long, or can be used more than once.

---

## Data Handling

### Sensitive Data Exposure (CWE-200, CWE-312, CWE-798)

```python
# ❌ Secret committed to source
STRIPE_SECRET_KEY = "sk_live_abc123"

# ✅ Environment variable only
STRIPE_SECRET_KEY = os.environ["STRIPE_SECRET_KEY"]
```

Check that:

- Production responses do not return stack traces.
- API responses do not include password hashes or tokens.
- PII is not written to logs or analytics.
- `.env` is in `.gitignore`.
- Backups and exports have access control.

### Path Traversal (CWE-22)

Look for user-controlled path parts that reach `open`, `readFile`, `sendFile`, `os.path.join`, or
archive extraction (`zip-slip`). Get the absolute path. Check that it stays inside the
expected base folder. Removing `../` with a string replace is not enough.

### SSRF (CWE-918)

```js
// ❌ Attacker passes http://169.254.169.254/latest/meta-data/
const data = await fetch(req.query.webhook);

// ✅ Hostname allowlist — parse and verify before fetching
const parsed = new URL(req.query.webhook);
if (!ALLOWED_DOMAINS.includes(parsed.hostname))
  throw new Error("Disallowed domain");
const data = await fetch(req.query.webhook);
```

High-risk places: webhook setup, URL previews, PDF/screenshot generators, image
proxies, importers. Also block redirects to internal IP ranges and `file://` / `gopher://`.

### Insecure Deserialization (CWE-502)

Look for these on untrusted bytes: `pickle.loads`, `yaml.load` without `SafeLoader`, `ObjectInputStream`, PHP `unserialize`,
`Marshal.load` (Ruby), and `JsonConvert` with `TypeNameHandling.All`.

### XXE (CWE-611)

Look for XML parsers that load external entities. Turn off DTDs and external entities
on purpose (`libxml_disable_entity_loader`, `XMLConstants.FEATURE_SECURE_PROCESSING`,
`defusedxml`).

### Transport & Storage

- No TLS on internal service calls. Also `rejectUnauthorized: false`, `verify=False`,
  `InsecureSkipVerify: true`.
- Secrets or PII saved without encryption. Passwords hashed with a fast algorithm instead
  of bcrypt/scrypt/Argon2.

---

## Cryptography

- MD5, SHA1, or DES used for a security purpose (signatures, password hashing, tokens).
- Hardcoded IVs, salts, or keys. The same IV used for many encryptions.
- ECB mode. Encryption without authentication (use AES-GCM or encrypt-then-MAC).
- `Math.random()`, `rand()`, or a time-seeded PRNG that makes tokens, session IDs, OTPs, or
  password-reset links. Use a secure random generator (CSPRNG) instead (`crypto.randomBytes`, `secrets`, `SecureRandom`).
- Comparing secrets or MACs in a way where the time depends on the input (`==` instead of `timingSafeEqual`).

---

## Business Logic

- **Race conditions (TOCTOU)** — "check, then act" on balances, coupon use, stock,
  or duplicate requests, with no transaction, row lock, or unique constraint.
- **Integer/float issues** — floats for money. Overflow or negative amounts in
  money math. No min/max checks on amounts the user sends.
- **Missing rate limiting** — on login, password reset, OTP, signup, and any endpoint that is
  costly or calls outside services.
- **Easy-to-guess IDs** — sequential IDs on sensitive data, with no
  owner check. This leads straight to IDOR.
- **Workflow bypass** — an endpoint that lets a client skip a required step (payment,
  verification, approval).

---

## Input Validation

Check shape and type at every entry point. Use a schema library (Zod, Joi, Pydantic,
Bean Validation). Unchecked input that reaches any sink above is always a finding. Never
accept secrets in query parameters. They end up in logs and referrers. Use headers instead.
