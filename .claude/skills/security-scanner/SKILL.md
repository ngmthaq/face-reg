---
name: security-scanner
description: "Security Scanner — AI security check that reads code like a security researcher: follows data flows, understands how parts work together, and finds security bugs that pattern-matching tools miss. Covers dependency CVEs (SCA), static analysis (SAST), injection flaws (SQLi, XSS, Command Injection, SSRF), broken auth and access control (IDOR/BOLA, JWT, CSRF, mass assignment), hardcoded secrets and credential exposure, weak cryptography, business logic bugs, and AI/LLM threats (prompt injection, tool abuse, data exfiltration). Use when: scanning or auditing a codebase, reviewing a diff or PR for security, checking for secrets or leaked credentials, hardening code, or any casual phrasing like 'is my code secure?', 'any vulnerabilities here?', 'check my repo', /security-scanner."
---

# Security Scanner

> **Writing style:** Follow the writing rules in [AGENT_RULES](../../references/AGENT_RULES.md) for all text you write — chat messages, questions, plans, reports, and generated docs.

A clear workflow you can repeat to find, check, rank, and fix security problems
(vulnerabilities) in any codebase.

Static analysis tools only match patterns. This skill does more:

1. **Reads code like a security researcher** — understands context, purpose, and data flow.
2. **Follows data across files** — tracks how untrusted input moves through the app.
3. **Checks its own findings** — looks at each result again to remove false alarms.
4. **Assigns severity** — CRITICAL / HIGH / MEDIUM / LOW / INFO.
5. **Suggests exact patches** — every finding comes with a real fix.
6. **Needs human approval** — nothing is changed on its own; the user reviews first.

## When to Use

- Scanning a codebase, folder, or single file for security problems
- Reviewing a diff, commit, or pull request before merge
- Looking for hardcoded secrets, API keys, or credentials in code, config, CI/CD, or IaC
- Checking dependencies for known CVEs
- Reviewing authentication, authorization, or access control logic
- Following user input from an entry point to a dangerous sink (a place where input is used, like a DB query)
- Checking AI agent / LLM code for prompt injection and unsafe tool use
- Any request like "is this safe?", "audit this", "check for vulnerabilities"

---

## Execution Workflow

Follow these steps **in order** every time.

### Step 1 — Find the Scope and Look Around

Decide what to scan:

- If a path was given (`/security-scanner src/auth/`), scan only that path.
- If the task is a diff or PR, scan **only the changed lines** — not the whole repo.
- If not, scan the whole project from the root.

Then list the attack surface (all places an attacker can reach): languages and runtimes, dependency manifests (`package.json`,
`requirements.txt`, `go.mod`, `*.csproj`, `Gemfile`, `pom.xml`, `Cargo.toml`,
`composer.json`), lockfiles, framework signs, HTTP/CLI/queue entry points, and trust
boundaries — where does untrusted data come in?

Load [`references/language-patterns.md`](./references/language-patterns.md) for the
framework patterns that match the stack you found.

**Write this before you go on:** a one-paragraph threat model (who can attack, and where). Example:

> "Node.js/Express API. Untrusted input enters via `req.body` and `req.query`. Three sinks:
> a PostgreSQL query builder, an `exec()` call in the export service, and an OpenAI prompt
> in the summarization endpoint. Auth is JWT with no role enforcement on admin routes."

### Step 2 — Dependency Audit (SCA)

Check dependencies first — quick results before you read the code.

```bash
npm audit --json                      # Node.js
pip-audit --format=json               # Python
govulncheck ./...                     # Go
dotnet list package --vulnerable      # .NET
bundle-audit check --update           # Ruby
mvn dependency-check:check            # Java
cargo audit                           # Rust
```

Flag CVEs with CVSS ≥ 7.0, problems in indirect dependencies, old crypto libraries, and
locked versions that have no fix yet. Lower the severity for `devDependencies` that never
go to production. When no tool is available, check the package files against the watchlist in
[`references/vulnerable-packages.md`](./references/vulnerable-packages.md).

### Step 3 — Secrets & Exposure Scan

Run the included scanner — **really run it**, do not fake the output:

```bash
chmod +x .claude/skills/security-scanner/scripts/scan-secrets.sh

# Diff mode (best for reviews) — checks only added lines
git diff --cached | .claude/skills/security-scanner/scripts/scan-secrets.sh --diff
git diff         | .claude/skills/security-scanner/scripts/scan-secrets.sh --diff
git show         | .claude/skills/security-scanner/scripts/scan-secrets.sh --diff

# File mode (full-codebase audit)
.claude/skills/security-scanner/scripts/scan-secrets.sh path/to/file.env path/to/config.py
```

| Exit code | Meaning                                     |
| --------- | ------------------------------------------- |
| `0`       | No secrets detected                         |
| `1`       | One or more secrets found — **block merge** |

The script finds cloud keys, GitHub tokens, private keys, connection strings, SaaS keys,
and JWTs. Also check config, `.env`, CI/CD workflows, Dockerfiles, and IaC by hand with
[`references/secret-patterns.md`](./references/secret-patterns.md)
— including entropy checks (random-looking strings) and secrets in comments, debug logs, or git history.

> **Never print a secret value in full.** Report only its type, location, and a
> masked prefix.

### Step 4 — Static Analysis (SAST)

```bash
semgrep --config=auto --json .
```

Enable rule sets `p/owasp-top-ten`, `p/secrets`, `p/jwt`, `p/sql-injection`, `p/xss`, plus
the language pack (`p/nodejs`, `p/python`, `p/java`). Add targeted grep searches for
what Semgrep misses:

```bash
grep -rn "password\s*=\s*['\"]"    --include="*.py" --include="*.js"
grep -rn "eval("                    --include="*.js"
grep -rn "os\.system\|shell=True"   --include="*.py"
grep -rn "dangerouslySetInnerHTML"  --include="*.jsx" --include="*.tsx"
```

If you cannot run external tools (offline, sandboxed, or during a PR review), use
the same rules by reading the code yourself — the deep scan in Step 5 is the backup.

### Step 5 — Vulnerability Deep Scan

This is the main step. Think about the code; do not just match patterns. Follow
`[source] → [processing] → [sink]` for every untrusted input.

All the signs to look for, safe patterns, and extra checks are in
[`references/vuln-categories.md`](./references/vuln-categories.md):

- **Injection** — SQLi (incl. second-order), XSS, command injection, LDAP/XPath/header/log injection, template injection
- **Auth & access control** — missing authn, IDOR/BOLA, JWT weaknesses (`alg:none`, weak secret, no expiry), session fixation, CSRF, privilege escalation, mass assignment
- **Data handling** — sensitive data in logs/errors/responses, missing encryption in transit or at rest, insecure deserialization, path traversal, XXE, SSRF
- **Cryptography** — MD5/SHA1/DES for security purposes, hardcoded IVs or salts, `Math.random()` for tokens, disabled TLS verification
- **Business logic** — race conditions (TOCTOU), integer overflow in financial math, missing rate limiting, predictable identifiers
- **API surface** — unvalidated input at entry points, secrets in query parameters, missing schema validation

### Step 6 — AI / LLM Security

Run this step when the codebase calls an LLM, builds an agent, or builds a RAG pipeline.
Details in [`references/ai-llm-security.md`](./references/ai-llm-security.md):

- **Prompt injection** — user input is put inside system prompts instead of being kept in its own role
- **Insecure tool use** — LLM output picks/calls tools without an allowlist and without typed argument checks
- **Data leakage** — DB rows, PII, or file contents sent to a third-party provider without hiding private parts
- **Indirect prompt injection** — instructions hidden in fetched pages or retrieved documents

**Rule:** LLM output is untrusted input. Check it the same way you check `req.body`.

### Step 7 — Cross-File Data Flow Analysis

After you check each file, look at the whole system:

- Follow user-controlled input from entry points (HTTP params, headers, body, uploads) all
  the way to sinks (DB queries, `exec` calls, HTML output, file writes, LLM prompts).
- Find security problems that you can only see when you read several files together.
- Check trust boundaries between services, modules, and internal APIs.

### Step 8 — Check Your Own Findings

For **each** finding:

1. Re-read the relevant code with fresh eyes.
2. Ask: can an attacker really use this, or is there input cleaning I missed?
3. Check if a framework or middleware already handles it earlier in the flow.
4. Remove or lower anything that is not a real security problem.
5. Give a final severity and a confidence rating (High / Medium / Low).

### Step 9 — Report

Write the report in the exact structure from
[`references/report-format.md`](./references/report-format.md) — a severity summary table
first, then finding cards grouped by category.

### Step 10 — Propose Patches

For every CRITICAL and HIGH finding, write a real patch: the unsafe code
(before), the fixed code (after), what changed and why, and what to test to confirm the
fix. Keep the original code style, variable names, and structure.

Safe to auto-fix when asked: `npm audit fix`, patch-level dependency updates. Check first:
`npm audit fix --force` (major version jumps that can break code). Fix by hand only: anything about logic —
broken auth, IDOR, SSRF allowlists, prompt injection.

Say clearly: **"Review each patch before applying. Nothing has been changed yet."**

---

## Severity Guide

| Severity                   | Criteria                                                              | Example                          | CI Gate                 |
| -------------------------- | --------------------------------------------------------------------- | -------------------------------- | ----------------------- |
| 🔴 **CRITICAL**            | Can be attacked remotely, no login needed; data leak is likely        | Unauthed SQLi, RCE, auth bypass  | Block merge             |
| 🟠 **HIGH**                | Real attack path, big impact                                          | Stored XSS, IDOR, live secret    | Warn; requires approval |
| 🟡 **MEDIUM**              | Can be attacked only under some conditions or with other bugs         | CSRF, open redirect, weak crypto | Report only             |
| 🔵 **LOW**                 | Best practice missing, extra layer of safety                          | Verbose errors, missing headers  | Report only             |
| ⚪ **INFO**                | Small cleanup or monitoring note                                      | Outdated dep with no CVE         | Report only             |
| ⚫ **NEEDS MANUAL REVIEW** | Sink can be reached, but the input shape is unclear from reading code | Dynamic dispatch into a query    | Escalate before merge   |

Lower the severity when the path is behind strong authentication. Raise it when the finding is in a
payment flow, auth system, or PII handler.

---

## Rules

- **Never** apply a patch on your own — show it for human review.
- **Never** print a full secret value; mask it.
- **Always** start with the findings summary table (counts by severity).
- **Always** include file path, line number, and the exact vulnerable snippet.
- **Always** attach a confidence rating per finding, and group findings by category — not by file.
- **Explain the risk in plain English** — what can an attacker really do?
- **Do not mark code as secure or a task as complete** while any CRITICAL or HIGH finding is
  not fixed, or while `scan-secrets.sh` exits `1`.
- If nothing is found, say it plainly — "No vulnerabilities found" — and list what was scanned.

---

## Reference Files

| Reference                                                     | Load when                                                                             |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| [vuln-categories.md](./references/vuln-categories.md)         | Step 5 — signs to look for, unsafe vs. safe code, and extra checks for each category  |
| [secret-patterns.md](./references/secret-patterns.md)         | Step 3 — regex patterns, entropy checks, CI/CD and IaC secret risks, how to fix leaks |
| [language-patterns.md](./references/language-patterns.md)     | Step 1 — framework sinks for JS/TS, Python, Java, PHP, Go, Ruby, Rust, .NET           |
| [vulnerable-packages.md](./references/vulnerable-packages.md) | Step 2 — chosen CVE watchlist for npm, pip, Maven, RubyGems, Cargo, Go modules        |
| [ai-llm-security.md](./references/ai-llm-security.md)         | Step 6 — prompt injection, tool abuse, data exfiltration, agentic and RAG threats     |
| [report-format.md](./references/report-format.md)             | Step 9 — finding card template, summary block, patch format                           |
