# Step 2 — Coding Conventions

**Goal:** Find the project's coding rules and write them down. First, read [CODING_CONVENTIONS.md](../../../references/CODING_CONVENTIONS.md) to see what is already there. At the end, write the approved rules to the same file.

1. **Look** in the repo for coding rules:
   - Naming: camelCase, snake_case, or PascalCase for files, variables, functions, and classes
   - Folder structure: by feature, by layer, or by domain
   - Imports: absolute or relative paths, barrel files (`index.ts`)
   - Style config files: `.eslintrc.*`, `.prettierrc.*`, `pyproject.toml [tool.ruff]`, `.editorconfig`, `rustfmt.toml`
   - Comments and docs: JSDoc, Python docstrings, inline comments
   - Error handling: try/catch, Result types, error boundaries
   - State management, if any

2. **Show** the rules to the user and ask:

   > "Here are the coding rules I found. Do you want to change anything, or are they OK?"

3. **Only after the user says OK**, write the rules to [CODING_CONVENTIONS.md](../../../references/CODING_CONVENTIONS.md).
