# Codex Clone (Python)

CLI-first Codex-like agent scaffold using LangGraph + LangChain + langchain-openai. The current state focuses on quality gates, tooling, and placeholders for the full Codex toolset and workflow engine.

## Status
- Skeleton only: tools/agent/workflows are stubs awaiting full implementations.
- Quality gates enforced: strict typing (mypy), lint/format (ruff), per-file coverage ≥80%.

## Prerequisites
- Python 3.12
- Poetry (recommended)

## Setup & Usage
1) Install deps: `poetry install`  
2) CLI help: `poetry run codex --help`  
3) Run a prompt (stub): `poetry run codex run "hello"`  
4) Run a workflow (stub): `poetry run codex workflow examples/demo.yaml`
5) Interactive console: `poetry run codex` then type prompts; `exit` to quit.

### Using a virtual environment (recommended)
If you want an isolated env without touching global Python:
1) Create and activate:  
   - `python3 -m venv .venv`  
   - `source .venv/bin/activate`
2) Upgrade pip and install Poetry inside the venv:  
   - `pip install --upgrade pip`  
   - `pip install poetry`
3) Install project deps (still uses Poetry, but now inside your venv):  
   - `poetry install`
4) Run commands as usual:  
   - `poetry run codex --help` or any of the commands above.

## Dev Commands
- Lint: `poetry run ruff check`
- Format: `poetry run ruff format`
- Type check (source only): `poetry run mypy src`
- Tests + coverage: `poetry run pytest`
- Per-file coverage gate: `poetry run python scripts/check_coverage.py coverage.json --threshold 80`

## Quality Gates
- Pytest writes `coverage.json`; gate script ensures every source file stays ≥80% covered.
- Strict mypy on `src/codex`; tests excluded from typing.
- Ruff enforces import order and basic lint rules.

## Project Layout
- `src/codex/` — CLI (`cli.py`), config, logging, agent stubs, tools, workflows, DB helpers.
- `tests/` — unit coverage for current surface.
- `docs/` — requirements/design (see `docs/functional/requirements/REQUIREMENTS_v00.md`).
- `scripts/` — automation utilities (coverage gate).

## Next Steps
- Implement Codex-parity tools (fs, git, http, search, summarize).
- Build LangGraph agent assembly and workflow compiler.
- Add examples and integration tests mirroring original Codex behaviors.
