# Architecture

## Overview
- Goal: CLI-first Codex clone using LangGraph + LangChain + langchain-openai with Codex-parity tools, YAML/JSON workflows, SQLite persistence, and strict quality gates.
- Current state: scaffolding with tested stubs; no agent execution yet.

## Components
- `codex.cli`: Typer-based CLI entry; commands `run`, `workflow`, `tools`.
- `codex.config`: Pydantic settings loader (env/`.env`), model/timeout/safety flags.
- `codex.logging`: JSON logger setup; root handler to stdout.
- `codex.tools.*`: Tool interfaces (base + shell stub) matching Codex-like signatures.
- `codex.workflows.compiler`: Placeholder loader/compiler from YAML/JSON to LangGraph DAG.
- `codex.agent.runner`: Future LangGraph assembly and execution loop.
- `codex.db.session`: SQLite engine/session helpers (SQLModel/SQLAlchemy).

## Control Flow (target design)
1) CLI parses flags → loads settings → configures logging.
2) For `run`: build LangGraph graph (planner + tool executor) → stream steps → persist run metadata.
3) For `workflow`: load workflow doc → validate schema → compile to graph → execute.
4) Tool calls: routed via registry; safety warnings for destructive ops.
5) Persistence: SQLite records runs, tool invocations, workflow defs; artifacts stored in workspace FS.

## Workflows (planned)
- Input: YAML/JSON describing steps, tools, conditionals.
- Validation: pydantic models; versioned schema.
- Compilation: translate nodes/edges to LangGraph; variables passed via context.

## Tools (planned parity)
- Shell, filesystem, git, HTTP, search, summarize/analysis; consistent ToolSpec signatures; allowlists and confirmations for risky actions.

## Quality Gates
- Strict mypy on `src/codex`; tests skipped from typing.
- Ruff for lint/format.
- Pytest with coverage json; `scripts/check_coverage.py` enforces ≥80% per source file.

## Persistence & Config
- Default DB: `sqlite:///codex.db`; migration path via SQLModel/Alembic later.
- Settings precedence: env > `.env` > defaults; key `OPENAI_API_KEY` required for live runs.

## Roadmap
- Implement full toolset with safety guards.
- Build LangGraph agent loop + OpenAI client wiring.
- Workflow compiler + examples.
- Expand integration/parity tests and add CI.
