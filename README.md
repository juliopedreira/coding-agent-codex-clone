# Codax (Python)

CLI-first coding assistant with LangGraph-inspired planner/executor, pluggable search, safety/approval controls, and hardened tool suite.

## Status
- Core tools, safety policy, search backends, workflow runner, and CLI console implemented.
- Quality gates enforced: strict typing (mypy), lint/format (ruff), per-file coverage ≥80%.

## Prerequisites
- Python 3.12
- Poetry (recommended)

## Setup & Usage
1) Install deps: `poetry install`  
2) CLI help: `poetry run codax --help`  
3) Run a prompt: `poetry run codax run "hello"`  
4) Run a workflow: `poetry run codax workflow examples/demo_workflow.yaml`
   - TTD example with LLM nodes + CEL templating and params:
     `poetry run codax workflow examples/ttd_workflow.yaml --FEATURE="Add a log in mechanism"`
5) Interactive console: `poetry run codax` then type prompts; `exit` to quit.  
   - Commands: `/model <name>`, `/reason <effort>`, `/safety <mode>`, `/search_backend <name>`, `/save`.

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
   - `poetry run codax --help` or any of the commands above.

## Dev Commands
- Lint: `poetry run ruff check`
- Format: `poetry run ruff format`
- Type check (source only): `poetry run mypy src`
- Tests + coverage: `poetry run pytest`
- Per-file coverage gate: `poetry run python scripts/check_coverage.py coverage.json --threshold 80`

## Quality Gates
- Pytest writes `coverage.json`; gate script ensures every source file stays ≥80% covered.
- Strict mypy on `src/codax`; tests excluded from typing.
- Ruff enforces import order and basic lint rules.

## Project Layout
- `src/codax/` — CLI, config, logging, agent runtime, tools, workflows, DB helpers.
- `tests/` — unit coverage for current surface.
- `docs/` — requirements/design (see `docs/functional/requirements/REQUIREMENTS_v00.md`).
- `scripts/` — automation utilities (coverage gate).

## Next Steps
- Expand examples and live-run guidance; enrich LangGraph planner and streaming UX.
