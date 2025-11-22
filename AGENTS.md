# Repository Guidelines

## Project Structure & Module Organization
- `docs/functional/requirements/` holds functional requirements; expand with design docs as features land.
- Planned layout: `src/codax/` for CLI, agent graph, tools; `tests/` for unit/integration and parity fixtures; `examples/` for sample workflows (YAML/JSON); `scripts/` for utilities.

## Build, Test, and Development Commands
- Install (dev): `poetry install` — sets up the virtualenv with all extras.
- Run CLI locally: `poetry run codax --help`.
- Tests w/ coverage: `poetry run pytest` (produces `coverage.json`).
- Per-file coverage gate (>80% each source file): `poetry run python scripts/check_coverage.py coverage.json --threshold 80`.
- Lint/format: `poetry run ruff check` ; `poetry run ruff format`.
- Type check (source only): `poetry run mypy`.

## Coding Style & Naming Conventions
- Python 3.12; prefer type hints everywhere; enable `from __future__ import annotations` if helpful.
- Modules: snake_case filenames; classes: CapWords; functions/vars: snake_case.
- Keep public tool interfaces matching original Codex signatures; avoid breaking CLI flags.
- Limit side effects in module top-level; use dependency injection for services (LLM, DB, logger).
- Source code must type-check cleanly under strict mypy; tests are excluded from typing requirements.

## Testing Guidelines
- Framework: pytest; place tests mirroring package paths under `tests/`.
- Name tests `test_<feature>.py`; use fixtures for parity transcripts and tool stubs.
- Require >80% line coverage per source file (enforced via coverage gate); add regression tests for bugfixes.
- Use deterministic mocks for LLM/search/http; avoid live network in CI.

## Commit & Pull Request Guidelines
- Commits: concise imperative subject (e.g., “Add functional requirements v00”); group related changes.
- Include short body when behavior changes or migrations occur.
- PRs: describe scope, testing performed (`pytest`, specific cases), linked issues/tasks; include CLI output or screenshots for UX-facing changes.

## Security & Configuration Tips
- Secrets via env vars (`OPENAI_API_KEY`); never commit `.env` or keys.
- When wiring tools, default to warnings on destructive commands; document any bypass flags.
- Prefer SQLite for local dev; keep migration scripts under version control.
