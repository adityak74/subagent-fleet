# Repository Guidelines

## Project Structure & Module Organization

This repository currently contains project documentation for `subagent-fleet`, a planned Python CLI for generating LiteLLM and Claude Code-style subagent configuration. Keep product intent in `README.md` and implementation details in `SPEC.md`.

The intended source layout is:

- `src/subagent_fleet/` for CLI and library code.
- `src/subagent_fleet/generators/` for LiteLLM, Claude agent, and env-file generation.
- `src/subagent_fleet/templates/` for Jinja templates such as `litellm_config.yaml.j2`.
- `examples/` for sample `fleet.yaml` and generated outputs.
- `tests/` for pytest tests, named by behavior or module.

## Build, Test, and Development Commands

Use `rtk` when running shell commands in this workspace.

- `rtk python -m pytest` runs the full test suite once tests exist.
- `rtk python -m pytest tests/test_config.py` runs a focused test file.
- `rtk python -m subagent_fleet.cli --help` checks CLI wiring during development.
- `rtk python -m pip install -e ".[dev]"` installs the package in editable mode once `pyproject.toml` is added.

## Coding Style & Naming Conventions

Use Python with a `src/` layout. Prefer typed, small modules with clear boundaries: config parsing in `config.py`, network discovery in `discovery.py`, health checks in `health.py`, and output generation in `generators/`. Use `snake_case` for functions, modules, and variables; `PascalCase` for Pydantic models; lowercase, filesystem-safe names for agents such as `planner` or `reviewer`.

Keep generated files clearly marked with a generated-file header. Do not hardcode machine-specific endpoints outside examples or test fixtures.

## Testing Guidelines

Use `pytest`. Put tests in `tests/` with names like `test_config.py` and functions like `test_rejects_unknown_model_reference`. Cover validation rules, CLI behavior, generator output, and HTTP error handling. Mock Ollama network calls rather than requiring live local models in unit tests.

## Commit & Pull Request Guidelines

The current history uses direct, imperative commit messages, for example `Initialize README for subagent-fleet project`. Keep commits focused and describe the user-visible change.

Pull requests should include a short summary, testing performed, linked issue if applicable, and generated-output examples when behavior changes. Include screenshots only for future UI or dashboard work.

## Security & Configuration Tips

Treat Ollama and LiteLLM endpoints as private-network services. Do not commit real API keys, LAN secrets, or machine-specific `.env` files. Prefer examples with placeholder hosts and tokens.
