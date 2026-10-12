# Graphify Setup

Graphify turns a repo (code, SQL schemas, docs, PDFs, images) into a knowledge graph. AI agents can search this graph, so they do not miss code context. See [graphify on GitHub](https://github.com/safishamsi/graphify).

## What you need

- Python 3.10+
- `uv` (best) or `pipx`

## Install

The package name is `graphifyy` (two y's). The command is `graphify`.

```bash
# Best
uv tool install graphifyy

# Other ways
pipx install graphifyy
pip install graphifyy
```

Extra readers (install only what the project needs):

```bash
uv tool install "graphifyy[sql]"     # SQL schemas
uv tool install "graphifyy[pdf]"     # PDF files
uv tool install "graphifyy[office]"  # .docx / .xlsx
uv tool install "graphifyy[all]"     # everything
```

## Add to Claude Code

Add Graphify as a skill for this project only:

```bash
graphify install --project
```

Run this once. Then the assistant can use the graph by itself.

This command writes its notes into a root `CLAUDE.md`. But in this project, all AI instructions live in `.claude/CLAUDE.md`. So:

1. Move the Graphify notes from the root `CLAUDE.md` to `.claude/CLAUDE.md`. Create the file if it does not exist.
2. Delete the root `CLAUDE.md`. It is now empty.

## Build the graph

```bash
graphify .                 # build the graph for this folder
graphify . --update        # read only the changed files again
graphify . --no-viz        # no HTML, only the report and JSON
```

This creates `graphify-out/` (`graph.html`, `GRAPH_REPORT.md`, `graph.json`). Commit `graphify-out/` so the whole team uses the same graph.

To read docs, PDFs, or images, Graphify needs an LLM API key. Set `ANTHROPIC_API_KEY` before you build. Code files are read on your machine. They are never sent to an API.

## Search the graph

```bash
graphify query "what connects auth to the database?"
graphify path "UserService" "DatabasePool"
graphify explain "RateLimiter"
```

## Keep it up to date (optional)

```bash
graphify hook install      # rebuild on every commit
```
