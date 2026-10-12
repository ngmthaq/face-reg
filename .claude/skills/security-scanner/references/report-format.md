# Report Format

Write the sections in this order. Start with the summary. Never start with the first finding.

---

## 1. Scan Summary

```text
Security Scan Summary
=====================
Scope    : <paths / diff range scanned>
Stack    : <languages, frameworks detected>
Tools    : scan-secrets.sh (exit N) · npm audit · semgrep · manual review

Findings — CRITICAL: N  HIGH: N  MEDIUM: N  LOW: N  INFO: N  NEEDS REVIEW: N

Top Issues:
  1. [CRITICAL] SQL Injection    — services/userService.js:87
  2. [HIGH]     Prompt Injection — agents/summaryAgent.js:34
  3. [HIGH]     Broken Auth      — routes/invoiceRouter.js:61
```

If you found nothing, say so clearly. List what you scanned:

```text
No vulnerabilities found.
Scanned: 214 files across src/ and config/ · dependencies (npm audit, 0 advisories)
       · secrets scan (exit 0) · manual review of 12 route handlers and 3 LLM call sites.
```

---

## 2. Finding Cards

Group by **category**, not by file. Write one card per finding:

```text
[SEC-001] SQL Injection
Severity   : CRITICAL          Confidence : High
Location   : services/userService.js:87        CWE: CWE-89
Summary    : User-supplied email is concatenated into a raw SQL query.
Impact     : An unauthenticated attacker can dump or modify the entire users table.
Evidence   :
    const q = "SELECT * FROM users WHERE email = '" + req.body.email + "'";
    const rows = await db.query(q);
Fix        :
    const rows = await db.query("SELECT * FROM users WHERE email = ?", [req.body.email]);
Effort     : Low
```

Field rules:

- **Severity** — CRITICAL / HIGH / MEDIUM / LOW / INFO / NEEDS MANUAL REVIEW.
- **Confidence** — High / Medium / Low. Required on every finding.
- **Location** — always give the file path and line number. Use a range if the finding spans many lines.
- **Impact** — in plain English: what can the attacker really do? Do not just repeat the CWE name.
- **Evidence** — the exact unsafe code. Show only the lines that matter. Mask any secret.
- **Effort** — Low / Medium / High. This helps plan the fix.

For data-flow findings, add a line that shows the flow:

```text
Flow       : req.query.url (routes/webhook.js:12)
           → validateShape() [no host check] (lib/validate.js:40)
           → fetch() (services/fetcher.js:8)
```

---

## 3. Dependency Audit

Use one grouped table. Do not write a card per package:

```text
Dependency Findings
-------------------
Package         Current   Fixed     CVE              CVSS  Reachable  Scope
lodash          4.17.15   4.17.21   CVE-2020-8203    7.4   yes        runtime
jsonwebtoken    8.5.1     9.0.0     CVE-2022-23529   9.8   yes        runtime
minimist        1.2.0     1.2.6     CVE-2021-44906   9.8   no         dev
```

---

## 4. Secrets Scan

```text
Secrets Scan — scan-secrets.sh exit 1
-------------------------------------
[CRITICAL] AWS_ACCESS_KEY   config/deploy.yml:14    AKIA…XQ7A   (masked)
[HIGH]     GENERIC_SECRET   src/db/client.ts:9      "p4ss…"     (masked)

Action: rotate both credentials before removing them from source — the values are already
compromised. Then replace with environment variables and purge from git history.
```

---

## 5. Proposed Patches

For every CRITICAL and HIGH finding:

````text
[SEC-001] SQL Injection — services/userService.js:87

Before:
```js
const q = "SELECT * FROM users WHERE email = '" + req.body.email + "'";
const rows = await db.query(q);
```

After:
```js
// Parameterized query — the email is bound as data and can never alter the SQL.
const rows = await db.query("SELECT * FROM users WHERE email = ?", [req.body.email]);
```

Changed : String concatenation replaced with a bound parameter.
Verify  : Send an email value of `' OR 1=1 --` and confirm zero rows are returned.
````

Keep the original code style, variable names, and structure. Add a short comment
that explains the fix.

End the section with this exact text:

> **Review each patch before applying. Nothing has been changed yet.**
