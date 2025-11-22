# Architecture

## Overview
- Goal: CLI-first Codax agent using LangGraph-style planner/executor with Codax-parity tools, YAML/JSON workflows, pluggable search, and strict quality gates.
- Current state: working CLI/runtime with safety policy, workflow runner, search backends, and tested tool suite; SQLite helper remains optional, file-based state under `~/.codax/`.

## Components
- `codax.cli`: Typer-based CLI entry; commands `run`, `workflow`, `tools`.
- `codax.config`: Pydantic settings loader (env/`.env`), model/timeout/safety flags.
- `codax.logging`: JSON logger with rotation and redaction; stdout reserved for stream.
- `codax.tools.*`: Tool interfaces (shell/fs/git/http/search/text/workflow) with safety hooks.
- `codax.workflows.compiler`: Loads/compiles workflow docs to a runnable wrapper.
- `codax.agent.runner`: Minimal planner/executor graph that analyzes and summarizes prompts.
- `codax.db.session`: SQLite engine/session helpers (optional).

## Control Flow (target design)
1) CLI parses flags → loads settings from env/TOML → configures logging.
2) For `run`: build agent graph (planner + executor) → run analysis/summarization → stream tokens.
3) For `workflow`: load workflow doc → validate schema → execute steps with registry and context.
4) Tool calls: routed via registry; safety policy gates risky actions/commits; network toggle respected.
5) Persistence: file-based state under `~/.codax/`; SQLite helper available but not required.

## Workflows (planned)
- Input: YAML/JSON describing steps, tools, conditionals.
- Validation: lightweight schema check (steps list); versioned schema planned.
- Compilation: runnable wrapper invoking workflow tool runner; variables passed via context.

## Tools (planned parity)
- Shell, filesystem, git, HTTP, search (OpenAI/DDG), summarize/analysis; consistent signatures; safety approval hooks.

## Quality Gates
- Strict mypy on `src/codax`; tests skipped from typing.
- Ruff for lint/format.
- Pytest with coverage json; `scripts/check_coverage.py` enforces ≥80% per source file.

## Persistence & Config
- Default state: files under `~/.codax/` (config/logs); optional DB `sqlite:///~/.codax/codax.db`.
- Settings precedence: init > TOML config > env; OpenAI key optional (used when set).

## Roadmap
- Implement full toolset with safety guards.
- Build LangGraph agent loop + OpenAI client wiring.
- Workflow compiler + examples.
- Expand integration/parity tests and add CI.
