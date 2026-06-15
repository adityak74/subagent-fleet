---
name: subagent-fleet-bootstrap
description: Install the subagent-fleet CLI first, then set up assistant skills and fleet config.
---

# subagent-fleet bootstrap

Use this skill when `subagent-fleet` has been installed as an assistant plugin or skill before the Python CLI is available on the user's machine.

## Goal

Get the CLI installed, verify it works, install the assistant-facing skills into the current repo, then continue with fleet setup.

## Install the CLI

First check whether the CLI already exists:

```bash
subagent-fleet --help
```

If it is missing and the current repository is `subagent-fleet`, install from the checkout:

```bash
python -m pip install -e ".[dev]"
```

If the user is in a different project, install from GitHub:

```bash
python -m pip install "git+https://github.com/adityak74/subagent-fleet.git"
```

If the user prefers isolated CLI tools and has `pipx`, use:

```bash
pipx install "git+https://github.com/adityak74/subagent-fleet.git"
```

## Verify

```bash
subagent-fleet --help
subagent-fleet skills list
```

## Install Repo-Local Assistant Skills

Install the skills for Claude Code, Codex, and OpenCode in the current project:

```bash
subagent-fleet skills install
```

Use a narrower target if the user asks:

```bash
subagent-fleet skills install --target claude-code
subagent-fleet skills install --target codex
subagent-fleet skills install --target opencode
```

## Continue Setup

After the CLI exists, continue with:

```bash
subagent-fleet init
subagent-fleet validate
subagent-fleet discover
subagent-fleet generate
subagent-fleet status
```

Do not expose Ollama or LiteLLM to the public internet. Prefer LAN, firewall rules, Tailscale, WireGuard, or a private subnet.
