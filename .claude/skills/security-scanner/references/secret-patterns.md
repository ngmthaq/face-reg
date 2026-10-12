# Secret Patterns

The main pattern list is in
[`../scripts/scan-secrets.sh`](../scripts/scan-secrets.sh). Run it first. This file
explains what the script finds, what it cannot find, and how to fix a leak.

> **Never print a secret value in full.** Report only its type, location, severity, and a
> masked prefix (`sk_live_abc1…`).

---

## Running the Scanner

```bash
chmod +x .claude/skills/security-scanner/scripts/scan-secrets.sh

# Diff mode — inspects only added (+) lines; ignores removals and context
git diff --cached | .claude/skills/security-scanner/scripts/scan-secrets.sh --diff
git diff         | .claude/skills/security-scanner/scripts/scan-secrets.sh --diff
git show         | .claude/skills/security-scanner/scripts/scan-secrets.sh --diff

# File mode — full audit of specific files
.claude/skills/security-scanner/scripts/scan-secrets.sh .env config/settings.py
```

Use diff mode during reviews. It keeps CI fast and reports only new problems.
Exit `0` = clean. Exit `1` = findings, so block the merge.

---

## Detected Patterns

| Type                      | Severity | Signature                                                    |
| ------------------------- | -------- | ------------------------------------------------------------ |
| AWS access key            | CRITICAL | `AKIA` + 16 uppercase alphanumerics                          |
| AWS secret key            | CRITICAL | `aws_secret_access_key = <40 base64 chars>`                  |
| GCP service account       | CRITICAL | `"type": "service_account"` in JSON                          |
| GCP API key               | HIGH     | `AIza` + 35 chars                                            |
| Azure client secret       | CRITICAL | `azure_client_secret = <34+ chars>`                          |
| GitHub tokens             | CRITICAL | `ghp_` / `gho_` / `ghs_` / `ghr_` + 36, `github_pat_` + 82   |
| Private keys              | CRITICAL | `-----BEGIN (RSA\|EC\|OPENSSH\|DSA\|PGP) PRIVATE KEY-----`   |
| Stripe secret             | CRITICAL | `sk_live_` + 24+; restricted `rk_live_` = HIGH               |
| Slack token / webhook     | HIGH     | `xox[baprs]-…` / `hooks.slack.com/services/…`                |
| Discord bot token         | HIGH     | `[MN]<23+>.<6>.<27+>`                                        |
| Twilio API key            | HIGH     | `SK` + 32 hex                                                |
| SendGrid API key          | HIGH     | `SG.<22>.<43>`                                               |
| npm token                 | HIGH     | `npm_` + 36                                                  |
| Generic secret assignment | HIGH     | `(secret\|token\|password\|api_key\|client_secret) = "<8+>"` |
| DB connection string      | HIGH     | `mongodb\|postgres\|mysql\|redis\|amqp\|mssql://…`           |
| Bearer / JWT              | MEDIUM   | `Bearer <jwt>` / `eyJ….eyJ….<sig>`                           |
| Internal IP + port        | MEDIUM   | RFC1918 address with an explicit port                        |

---

## What the Script Cannot Find — Check by Hand

**Random-looking strings with no known prefix.** Flag a string if all of these are true:

- It has 20+ characters.
- It mixes upper case, lower case, and digits.
- It has a security-like name (key, token, secret).
- It is not a hash of test data or a base64 test value.

Shannon entropy above 4.0 bits/char for base64 (or above 3.0 for hex) is a strong sign.

**Risky places:**

- `.env`, `.env.local`, `.env.production` committed to the repo. Check `git ls-files`, not
  only the working tree. Check that `.gitignore` covers them.
- **CI/CD** — `.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`. Look for: literal values in `env:`
  blocks, secrets printed in logs, `pull_request_target` used with a checkout of
  untrusted refs, and third-party actions not locked to a version (`uses: foo/bar@main`).
- **Docker** — `ENV`/`ARG` with credentials (they stay in image layers forever), `.dockerignore`
  without `.env`, and secrets in `RUN` commands.
- **IaC** — Terraform `.tfvars` and state files, Kubernetes `Secret` manifests with plain
  base64 (base64 is not encryption), Helm `values.yaml`, and Ansible vars.
- **Client bundles** — keys in `NEXT_PUBLIC_*`, `REACT_APP_*`, `VITE_*`, mobile app code,
  or anything sent to the browser.
- **Comments, docstrings, debug logs, test fixtures, README examples** — people often paste real
  credentials in all of these.
- **Git history** — a secret deleted in a later commit is still leaked, and it still works. To find out
  if a key must be changed, check `git log -p -S '<masked-prefix>'`.

**False alarms to ignore:** known placeholder values (`sk_test_…`, `AKIAIOSFODNN7EXAMPLE`,
`xxx`, `changeme`, `<your-key-here>`), example keys in vendor docs, and test values that
are clearly fake. If you are not sure, lower the severity. Do not quietly drop it.

---

## How to Fix

A real secret in the code is at least HIGH. A working production credential is CRITICAL.

1. **Rotate (replace) the key first.** The key is leaked as soon as it is committed. Deleting the
   line does not undo the leak. Rotate before you clean up.
2. **Use a reference instead.** Use an environment variable or a secrets manager (AWS Secrets
   Manager, GCP Secret Manager, HashiCorp Vault, GitHub Actions secrets, Doppler).
3. **Clean the git history** if the repo is or was public. Use `git filter-repo` or BFG. Then force-push
   and tell the other people on the repo.
4. **Add a guard.** Add a pre-commit hook that runs `scan-secrets.sh --diff`. Also turn on push
   protection on the git provider.
5. **Check for use.** Look in the provider logs for any access with the leaked key.
