INTRODUCTION
- Goal: Build a Python 3.12, CLI-first Codex clone using LangGraph + LangChain + langchain-openai. Provide the full original Codex toolset, YAML/JSON-authored workflows compiled to LangGraph, SQLite persistence, structured JSON logging, full-access tools with warnings, and single-agent sequential execution. Ship as a Poetry package under a privative license. Include both feature-level and parity tests.

ARCHITECTURE
- Layers: CLI entrypoint → command router → agent runner (LangGraph single-agent) → tool registry (Codex-parity tools) → LLM client (langchain-openai) → persistence (SQLite) → logging (JSON) → config loader (env + file).
- Graph flow: linear LangGraph plan/act loop (planner node → tool executor node → condition to continue or finish); no parallel branches.
- Storage: SQLite for runs, tool invocations, workflow definitions, and artifact metadata; workspace filesystem for artifacts.
- Config: environment variables plus optional config file (toml/yaml) for API keys, workspace paths, safety toggles, model settings.
- Safety posture: tools have host access; warn/confirm on risky operations (e.g., recursive delete, network POST to non-allowlisted hosts).
- Packaging: Poetry project; `codex` CLI installed via `poetry install`.
- Testing: pytest; split parity fixtures vs. feature unit/integration tests; test DB migrations; golden transcripts for CLI/agent flows.

FEATURES DESIGN

- LLM/Agent Core
  - Functional: Run user prompts through a single-agent loop with tool use; support temperature/max-tokens/stop sequences; streaming optional.
  - Technical: LangGraph nodes for planner (LLM) and tool executor; conditional edges for tool calls/completion; LangChain ChatOpenAI client; timeout handling and output truncation.
  - Tests: Mocked LLM to assert node ordering and messages; config override tests; timeout and streaming flags.

- Tool Registry (Codex parity)
  - Functional: Mirror original Codex tools and interfaces (shell exec, filesystem read/write/list, git status/diff/apply, HTTP fetch, search, analysis/summarize, etc.).
  - Technical: Uniform ToolSpec classes; synchronous wrappers; safety prompts for destructive flags; stdout/stderr capture; exit codes propagated; redaction of secrets in logs.
  - Tests: Parity fixtures comparing outputs for canonical commands; permission warning paths; non-zero exit propagation; log redaction checks.

- Shell Tool
  - Functional: Execute commands in workspace; capture stdout/stderr/exit; optional cwd.
  - Technical: Subprocess with timeout; output truncation; redact secrets; OS-agnostic; confirm on destructive patterns unless bypass flag set.
  - Tests: Simple commands; timeout path; large output truncation; destructive command warning; secret redaction.

- Filesystem Tools
  - Functional: read/write/append files, list, mkdir/rm, glob.
  - Technical: Path normalization to workspace; guard against traversal unless explicitly allowed; detect and block binary writes if needed; overwrite vs. append modes.
  - Tests: Path traversal attempts; overwrite vs. append behavior; binary file rejection; directory creation/deletion flows.

- Git Tools
  - Functional: status, diff, show, apply patch, list branches; commit optional (warning by default).
  - Technical: Use git CLI; apply_patch with validation; optional commit disabled or warned; support for repo path override.
  - Tests: Fixture repo; diff outputs; apply patch failure paths; dirty workspace warnings; branch listing.

- HTTP Tool
  - Functional: GET/POST with headers/body; JSON convenience; return status/body/headers with truncation.
  - Technical: httpx/requests with size/time limits; allowlist/denylist configurable; user-agent string; TLS verification on.
  - Tests: Mocked HTTP; large body truncation; non-2xx handling; allowlist/denylist behavior; timeout.

- Search Tool
  - Functional: Web search returning snippets/links.
  - Technical: Pluggable backend; default mocked/offline provider; optional real provider behind environment flag; rate-limit handling.
  - Tests: Mock provider outputs; empty result handling; rate-limit error path; provider selection logic.

- Analysis/Summarize Tool
  - Functional: Summarize text/file content; simple stats; optional chunking for long inputs.
  - Technical: Reuses LLM with prompt templates; chunk and merge strategy; non-UTF8 handling with fallback.
  - Tests: Deterministic mock LLM; chunk boundary coverage; non-UTF8 input path; prompt selection.

- Workflow Engine (YAML/JSON → LangGraph)
  - Functional: User-defined workflows describing steps, tools, and LLM calls; compile to LangGraph; run via CLI; support parameters and basic conditionals.
  - Technical: Versioned schema parsed to dataclasses; validation layer; compiler to graph nodes/edges; variable propagation; schema registry for future versions.
  - Tests: Schema validation success/failure; compile and run a sample workflow; bad config errors; variable passing across steps.

- Persistence (SQLite)
  - Functional: Record runs, tool invocations, workflow definitions, and artifact metadata.
  - Technical: SQLModel/SQLAlchemy; migrations via Alembic or lightweight DDL; indexes on run_id/timestamps; connection pool tuned for single-process use.
  - Tests: Migration smoke; CRUD for runs and workflows; concurrent insert within single process; rollback on failure.

- CLI
  - Functional: Commands: `codex run <prompt>`, `codex workflow run <file>`, `codex tools list`, `codex logs <run_id>`, `codex persist show`, `codex config check`.
  - Technical: Typer/Click-based; JSON output option; colored terminal output optional; dependency-injected services; supports verbose/debug flags.
  - Tests: CLI invocation via pytest + CliRunner; correct exit codes; JSON output validity; help text presence.

- Config/Auth
  - Functional: Load OpenAI key from env; optional config file; flags for safety, timeouts, model name; workspace path setting.
  - Technical: Pydantic settings; precedence env > CLI > file; validation for required keys; support `.env`.
  - Tests: Precedence ordering; missing key errors; default model selection; env file loading.

- Logging/Telemetry (JSON)
  - Functional: Structured logs to stdout/file; per-run correlation IDs; log tool invocations.
  - Technical: Stdlib logging with JSON formatter; log levels via CLI flags; secret redaction; optional file handler.
  - Tests: Log format schema; redaction; level filtering; file handler write.

- Safety/Warnings
  - Functional: Warn/confirm on destructive shell/fs ops; log all tool invocations; allow bypass with `--yes`.
  - Technical: Heuristic detection (`rm -rf`, overwrites); confirmation prompts; enforcement of denylist patterns; configurable in config.
  - Tests: Warning emitted; bypass flag works; denial on no-confirm; denylist hit.

FINAL CHECKLIST
- Confirmed choices: CLI-only; OpenAI via langchain-openai; Python 3.12; pytest; full Codex toolset; YAML/JSON workflows → LangGraph; SQLite; full-access tools with warnings; single-agent sequential; Poetry package; JSON logging; privative license; parity + feature tests.
- Define pyproject dependencies: langchain, langgraph, langchain-openai, typer/click, sqlmodel/sqlalchemy, httpx/requests, pytest, rich (optional), pydantic, json logging formatter, alembic (optional).
- Lock tool interfaces to original Codex signatures.
- Draft workflow schema and validation rules.
- Design DB schema and migration plan.
- Map CLI commands and options.
- Plan test suites: unit (tools, config), integration (agent loop), parity fixtures, CLI tests, DB tests.
- Decide mock strategy for LLM/search/http.
- Prepare docs: README, CLI usage, config samples, workflow examples, testing instructions, license notice.
- Note safety prompts and confirmations; default warnings for risky operations.
