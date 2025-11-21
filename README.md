# Codex Clone (Python)

CLI-first Codex-like agent scaffold using LangGraph + LangChain + langchain-openai. Current state is a skeleton ready for tool implementations, workflows, and agent wiring.

## Getting Started
1. Install dependencies (dev): `poetry install`
2. Run CLI help: `poetry run codex --help`

## Development Commands
- Lint: `poetry run ruff check`
- Format: `poetry run ruff format`
- Type check (source only): `poetry run mypy`
- Tests with coverage: `poetry run pytest`
- Per-file coverage gate: `poetry run python scripts/check_coverage.py coverage.json --threshold 80`

## Coverage & Quality Gates
- Pytest collects coverage for `src/codex` and writes `coverage.json`.
- `scripts/check_coverage.py` fails if any source file is below 80% line coverage.
- Source is type-checked under strict mypy settings; tests are excluded from type checking.

## Project Layout
- `src/codex/` — CLI, config, logging, agent stubs, tools, workflows, DB helpers.
- `tests/` — unit tests, parity/coverage scaffolding.
- `docs/` — requirements and design documents.
- `scripts/` — automation utilities (coverage gate).
