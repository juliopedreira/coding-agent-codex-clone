# MVP Requirements (Production-Ready)

## INTRODUCTION
- Goal: Ship a production-ready CLI-only Codex clone MVP on Linux using LangGraph + LangChain + langchain-openai with full Codex tool parity, YAML/JSON workflows, SQLite + tracked artifacts, JSON logging to stdout and file, and enforced quality gates.
- Scope decisions: OpenAI-only LLM; full host access tools with warnings (no confirmations); artifacts stored under `artifacts/<run_id>/`; per-file coverage ≥80%; Poetry packaging only; no external deadlines.

## ARCHITECTURE
- Layers: CLI (Typer) → Config/Logging → Agent Runner (LangGraph single-agent) → Tool Registry (Codex parity) → OpenAI client → Persistence (SQLite + artifact index) → JSON Logging.
- Storage: SQLite DB for runs, tool calls, workflow definitions, artifact metadata. Artifacts live in `./artifacts/<run_id>/`.
- Config: Env + `.env` + CLI flags for API key, model, temp, timeouts, workspace, log file path.
- Safety: Host access; destructive ops log warnings only (no prompts/allowlists by default). Secret redaction in logs.
- Packaging: Poetry; optional `poetry build` for wheel/sdist.
- Platform: Linux target (primary).
- Quality gates: Ruff lint/format; strict mypy on `src/codex`; pytest + per-file coverage ≥80% enforced by gate script.

## FEATURES DESIGN

### Agent Core (Single-Agent LangGraph)
- Functional: Run prompt via plan/act/observe loop; tools callable; stop on completion.
- Technical: Nodes for planner (LLM), tool executor, decision router; limited memory (conv + last tool); timeouts.
- Tests: Mock LLM; verify node transitions; timeout path; tool routing.

### Workflow Engine (YAML/JSON → LangGraph)
- Functional: Load workflow file, validate schema v1, compile to LangGraph DAG; parameters + simple conditionals.
- Technical: Pydantic schema; compiler emits nodes/edges; step types: LLM, tool, branch; uses same runtime as ad-hoc prompts.
- Tests: Good/bad schema; compile success; execution with mocked LLM/tools; variable passing.

### Tool Registry (Full Codex Parity)
- Functional: shell, filesystem, git, http, search, summarize/analysis with original signatures.
- Technical: Tool base/registry; safety warnings for destructive patterns; log every invocation; redact secrets.
- Tests: Happy/error cases per tool; warning emission; redaction; return code propagation.

### Shell Tool
- Functional: Execute commands in workspace; capture stdout/stderr/exit; optional cwd.
- Technical: Subprocess with timeout, truncation; warnings on risky commands; allowlist optional (off).
- Tests: Success, non-zero, timeout, truncation, risky warning.

### Filesystem Tools
- Functional: read/write/append, list, mkdir/rm, glob.
- Technical: Normalize paths to workspace; traversal guard; binary detection; overwrite vs append; warning on deletions.
- Tests: Traversal block; overwrite/append; binary rejection; mkdir/rm flows.

### Git Tools
- Functional: status, diff, show, apply patch, branch list; commit optional (warn).
- Technical: Wrap `git` CLI; validate patch input; repo root configurable.
- Tests: Fixture repo; diff output; apply patch success/fail; dirty tree warning.

### HTTP Tool
- Functional: GET/POST with headers/body; JSON convenience; return status/headers/body (truncated).
- Technical: `httpx` with timeouts/size limits; host allowlist off by default; TLS verify on.
- Tests: Mock httpx; non-2xx path; truncation; timeout; allowlist toggle.

### Search Tool
- Functional: Web search returning snippets/links; can be disabled via config.
- Technical: Pluggable backend; default provider chosen (OpenAI/Bing) with env credentials; rate-limit handling.
- Tests: Mock provider; empty results; rate-limit error; disable flag.

### Summarize/Analysis Tool
- Functional: Summarize text/files; simple stats; chunking for large inputs.
- Technical: LLM with prompts; chunk/merge; non-UTF8 fallback.
- Tests: Mock LLM; chunk boundary; binary rejection.

### Persistence (SQLite + Artifacts)
- Functional: Record runs/tool calls/workflow defs; track artifact metadata; write artifacts to `artifacts/<run_id>/`.
- Technical: SQLModel/Alembic migrations; indexes on run_id/time; helper to create artifact dirs.
- Tests: Migration smoke; CRUD; artifact path creation; single-process concurrency.

### Logging
- Functional: JSON logs to stdout and default file `logs/codex.log`; run correlation IDs.
- Technical: Dual handlers; level from CLI; secret redaction; rotation optional later.
- Tests: Log format; file write; redaction; level filtering.

### CLI
- Functional: `codex run <prompt>`, `codex workflow run <file>`, `codex tools list`, `codex logs <run_id>`, `codex config check`.
- Technical: Typer commands; JSON output mode; uses settings/services; Linux focused.
- Tests: CliRunner invocations; JSON flag; exit codes; config check output.

### Config/Auth
- Functional: Env/.env/flags; requires `OPENAI_API_KEY`; configure model/temp/timeouts/workspace/log file.
- Technical: Pydantic settings; precedence env > file > defaults; validation for required keys.
- Tests: Precedence; missing key error; defaults applied.

### Quality Gates
- Functional: Per-file coverage ≥80%; strict typing; ruff lint/format.
- Technical: pytest-cov config; coverage gate script; mypy strict on src; ruff in CI.
- Tests/CI: Run ruff, mypy, pytest, coverage gate in pipeline.

## FINAL CHECKLIST
- Confirm scope: CLI-only Linux; OpenAI-only; full toolset; YAML/JSON workflows; SQLite + tracked artifacts; logs stdout + `logs/codex.log`; warnings only for destructive ops.
- Finalize search backend choice and config flags.
- Define workflow schema v1 and example files.
- Implement LangGraph agent assembly and workflow compiler.
- Implement full tool registry with safety warnings and logging.
- Add migrations and DB schema for runs/tools/artifacts/workflows.
- Ensure tests keep per-file coverage ≥80%; update coverage gate paths.
- Update docs (README/ARCHITECTURE) with MVP details and commands.
- Package via Poetry; optional `poetry build` for releases.
