# Step 7 — Apply Security Scanner Review

Use the **[security-scanner](../../security-scanner/SKILL.md)** skill on the diff. Check the code yourself. Do not run outside SAST tools. But do run its `scripts/scan-secrets.sh --diff` on the diff.

For each finding, write down:

- **File and line range**
- **Severity**: `CRITICAL` / `HIGH` / `MEDIUM` / `LOW`
- **Confidence**: `High` / `Medium` / `Low`
- **CWE / OWASP category**
- **Explanation**
- **Fix** (with a code example)
