# RTK Setup

RTK is a CLI tool that cuts LLM token use by 60–90% on dev commands. It is one Rust program. It makes command output shorter before the assistant reads it. See [rtk on GitHub](https://github.com/rtk-ai/rtk/tree/develop).

## Install

```bash
# Homebrew (best)
brew install rtk

# Install script (Linux/macOS)
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh

# Cargo
cargo install --git https://github.com/rtk-ai/rtk
```

If you used the install script, make sure `~/.local/bin` is in your `PATH`. Check that it works:

```bash
rtk --version
```

## Add to Claude Code

```bash
rtk init -g                # Claude Code / Copilot (default), for all projects
rtk init -g --auto-patch   # no questions, for CI/CD
```

Restart Claude Code after this. This turns on the hook. The hook changes Bash commands to their RTK version (e.g. `git status` → `rtk git status`).

The hook does not work with Claude Code's own `Read`, `Grep`, and `Glob` tools. To save tokens there, use shell commands or call `rtk` directly.

## Common commands

```bash
rtk git status / log / diff   # short git output
rtk ls .                      # short folder tree
rtk grep "pattern" .          # search results in groups
rtk cargo test / pytest / jest / go test   # tests, shows only failures
rtk tsc / lint / ruff check   # build and lint, in groups
```

## Check savings

```bash
rtk gain            # token savings summary
rtk gain --graph    # graph of the last 30 days
rtk discover        # find places where you could save more
```

## Notes

- Config file: `~/.config/rtk/config.toml` (macOS: `~/Library/Application Support/rtk/config.toml`).
- Telemetry is off by default. Turn it on with `rtk telemetry enable`.
- On Windows, use WSL to get all features, including the hook.
