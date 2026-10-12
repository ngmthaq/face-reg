# Step 4 — Check That the Code Matches the Requirements

Use the PR title, description (body), and linked issues from Step 2. Compare them with the diff. Answer these questions:

| Question                                                      | How to check                                                                      |
| ------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Does each requirement in the description have code changes?   | Match each goal or acceptance criterion to at least one changed file or function. |
| Are there code changes that the description does not explain? | Flag them. They may be unrelated or risky.                                        |
| Does the description match what the code really does?         | Note any difference between what the PR says and what the code does.              |
| Are the linked issues or tickets done?                        | If issues are linked, check that the code does what they ask.                     |

For each gap or difference, write down:

- **Requirement** (quote it from the description or issue)
- **Status**: `Missing` / `Partial` / `Mismatch` / `Unexplained change`
- **Details** (which files or logic)
