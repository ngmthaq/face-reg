# CLAUDE

Read all the files linked below. They tell you about the project, and what to do and not do.

---

## PROJECT OVERVIEW

Basic facts about the project: name, what it does, languages, frameworks, main libraries,
package manager, and where the docs are - see [PROJECT_OVERVIEW](./references/PROJECT_OVERVIEW.md).

---

## CODING CONVENTIONS

The code rules for this project. Follow them when you write code, so all code looks the
same - see [CODING_CONVENTIONS](./references/CODING_CONVENTIONS.md)

---

## AGENT RULES

The "DO" and "DO NOT" rules. Use them to know what to do first when you get a task, and what
you must never do. It also has the writing style rules: use plain, simple English that everyone
can read - see [AGENT_RULES](./references/AGENT_RULES.md)

# graphify
- **graphify** (`.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`
When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
