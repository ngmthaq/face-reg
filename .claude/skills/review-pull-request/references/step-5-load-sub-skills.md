# Step 5 — Load Sub-Skills

Load the full sub-skill before you use it. Follow every rule and phase in it. Do not skim or skip steps.

| Sub-skill                                           | When to load                    |
| --------------------------------------------------- | ------------------------------- |
| [clean-code](../../clean-code/SKILL.md)             | Always                          |
| [security-scanner](../../security-scanner/SKILL.md) | Always                          |
| [aaa-testing](../../aaa-testing/SKILL.md)           | Only if the diff has test files |

> Run `security-scanner` on the diff only. Do the deep security scan and data-flow checks yourself. You do not need outside SAST tools. But do run `scripts/scan-secrets.sh --diff` on the diff.
