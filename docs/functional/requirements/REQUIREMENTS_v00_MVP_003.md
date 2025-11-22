# MVP Requirements v00 — Productionization & Safety (MVP_003)

## INTRODUCTION
- Goal: Graduate the codax (Coding Assistant) CLI from scaffold to production-ready agent with real OpenAI integration, pluggable search, safety/approval controls, richer workflows, streaming UX, hardened tools, and comprehensive tests. Replace remaining stubs; ensure all persisted state and branding live under `~/.codax/` (never `~/.codax/`). File-based state only; no database by default.

## ARCHITECTURE
- Layers: CLI (Typer) → session runtime (interactive console with slash commands, approvals, streaming renderer) → LangGraph planner + executor (configurable via YAML graph) → Tool registry (shell/fs/git/http/search/web_search/text/workflow) → OpenAI (langchain-openai) → Persistence (config/logs/workflow cache under `~/.codax/`) → optional Docker packaging.
- Config: Pydantic settings with TOML file at `~/.codax/config.toml`; merged with env/.env; CLI flags and slash commands override at runtime.
- Logging: Structured JSONL with rotation to `~/.codax/logs/`; stdout reserved for streamed agent/messages/events.
- Safety: Policy layer wrapping tools; modes toggleable at runtime (`/safety`). Approvals required for destructive/risky actions and git commits when mode demands; workspace-root enforcement.
- Search: Pluggable backend (OpenAI native `web_search` tool or DuckDuckGo JSON). Backend switchable via config and `/search_backend` at runtime; fallback if preferred backend fails.
- Workflows: YAML/JSON schema v1 with steps, params, assigns, conditionals, loops, retries; compiled to LangGraph DAG; callable via CLI aliases (`wf:<name>`).

## FEATURES DESIGN

### Config & Secrets
- Functional: Load/persist API key, model, reasoning effort, safety mode, search backend, workspace root, logging paths. Slash commands allow toggling safety/search/model/reasoning at runtime and persisting when requested.
- Technical: `BaseSettings` + TOML loader/merger; helpers to read/write config; validation and path expansion; versioned settings for future migrations.
- Tests: Precedence (env > CLI/slash > config file); missing key errors; toggles persist correctly; path expansion correctness and normalization.

### Logging & Telemetry
- Functional: JSONL logs to rotating files; include run/session IDs; optional verbose trace mode. Stdout remains clean except streamed agent output.
- Technical: Rotating file handler; secret redaction filter; contextual `extra` (run_id, session_id, tool name). Configurable log level.
- Tests: Log file creation/rotation; redaction; level filtering; JSON structure validity.

### Safety & Approvals
- Functional: Modes (`safe`, `on-request`, `off`) switchable via `/safety`; approvals required for risky shell/fs/git commit/network POST when mode requires; warnings otherwise.
- Technical: Policy middleware intercepts tool calls; risky heuristics (delete, patch, git commit, outbound POST, workspace traversal); approval callback that can auto-accept/decline per mode; deny/allow lists configurable.
- Tests: Matrix of modes vs actions; approval prompt path; denial path; traversal/escape attempts blocked; git commit gated.

### Agent Graph (LangGraph)
- Functional: Planner + executor nodes with retries/backoff and guardrails; configurable graph template via YAML; stops on completion or iteration limits.
- Technical: Planner node uses ChatOpenAI with tool calling; executor dispatches to registry; shared memory of conversation/history; retry/backoff policy on failures.
- Tests: Mocked LLM verifies node ordering, retries, and stop conditions; YAML override parsing and application.

### OpenAI Integration
- Functional: Real chat completions with streaming; supports tool calls (including `web_search` when backend selected); configurable model/temperature/timeouts.
- Technical: `langchain-openai` Chat model with streaming callbacks; tool schema registration; retry/backoff; token trimming to respect model limits.
- Tests: Mock client; streaming handler assertions; tool-call payload validation; timeout/retry paths.

### Search Backend (Pluggable)
- Functional: Backends: (1) OpenAI native `web_search` tool, (2) DuckDuckGo JSON. Select via config or `/search_backend`; fallback if preferred fails.
- Technical: Search interface with backend registry; DDG via httpx; OpenAI via responses-compatible tool call; normalization of results (title/url/snippet).
- Tests: Mock DDG transport; mock OpenAI tool; backend switch; failure fallback path; result normalization.

### Tools Suite
- Shell: Subprocess exec with timeout; cwd support; output capture; risky detection; approval hook.
- Filesystem: read/write/append/list/mkdir/rm/glob with workspace guard; binary detection on read; deletion warnings.
- Git: status/diff/show/apply_patch/branches; commit gated by config/approval.
- HTTP: GET/POST with headers/body; approval for risky POST when safety mode requires; truncation and timeouts.
- Text: summarize/analyze upgraded to LLM-backed with heuristic fallback and token limits.
- Workflows: validate/execute workflow files; context vars; transcripts.
- Technical: Shared Tool interface; registry built per settings/policy; truncation safeguards.
- Tests: Happy paths; failures (timeout, bad patch, traversal); approval-required branches; redaction where applicable.

### Workflows & Graph Templates
- Functional: Workflow files define steps, args, assign, conditionals, loops, retries; parameters passed via CLI (e.g., `wf:new_feature DESC="Add search"`); transcripts emitted.
- Technical: Pydantic schema v1; compiler to LangGraph DAG; Jinja-like var interpolation `{{var}}`; library of templates (new_feature, bugfix, refactor, test); alias mapping stored in config dir.
- Tests: Schema validation success/fail; param binding; conditional/loop execution; transcript correctness; failure short-circuit.

### CLI & UX
- Functional: Commands `codax run`, `codax workflow run`, `codax tools list`, `codax logs tail`, `codax config`; interactive console with slash commands (`/model`, `/reason`, `/safety`, `/search_backend`, `/help`). Streaming renderer for tokens and tool events; optional `--jsonl` to mirror log file.
- Technical: Typer commands; clean stdout except stream; session runtime maintains state (model, safety, backend); JSONL mirror matches log structure.
- Tests: CliRunner coverage for commands; streaming smoke test; slash commands mutate state; jsonl mirror correctness.

### Persistence & State
- Functional: File-based state under `~/.codax/` (config, auth, logs, workflow cache); no DB by default.
- Technical: Directory initialization with locking to avoid corruption; versioned config schema; migration hooks for future changes; workspace root enforcement.
- Tests: Init paths; migration noop; corruption handling; lock behavior under concurrent open.

### Packaging & Distribution
- Functional: Poetry install for dev; Docker image option for hermetic runs; docs describe usage.
- Technical: Dockerfile (python:3.12-slim) with entrypoint script; mounts `~/.codax`; optional live env vars.
- Tests: CI build job; docker run smoke with mocked keys; Poetry install smoke.

### Testing Strategy
- Functional: Unit + integration with mocked OpenAI/search/http (no live network in CI); optional manual live-smoke gated by env (`CODAX_LIVE=1`, `OPENAI_API_KEY`, `SEARCH_BACKEND=openai|ddg`).
- Technical: Pytest markers for live; VCR-like fixtures optional; coverage gate ≥80% per source file retained.
- Tests: Verify skips when env missing; coverage script passes; deterministic mocks for LLM/search/http/tools.

### Docs
- Functional: Update README/ARCHITECTURE and examples; document safety modes, config paths, workflow schema/templates, search backend switch, live-test instructions, Docker usage.
- Tests: (Optional) lint docs links; ensure example workflows parse.

## FINAL CHECKLIST
- All branding/state uses `~/.codax/`; no `codax` paths remain.
- Safety/approval modes enforce risky actions and git commits; toggle via slash commands.
- LangGraph planner + executor implemented (no stubs) with YAML-configurable template.
- OpenAI integration live with streaming and tool calls.
- Pluggable search (OpenAI `web_search`, DuckDuckGo) selectable at runtime with fallback.
- Tool suite hardened (timeouts, guardrails, truncation, workspace enforcement).
- Workflow schema v1 supports conditionals/loops/retries; CLI alias invocation works; sample templates shipped.
- Logging writes JSONL with rotation; stdout reserved for stream output.
- Tests: mocked unit/integration; optional live-smoke; per-file coverage gate intact.
- Packaging: Poetry-ready; Dockerfile present; docs refreshed with new features and paths.
