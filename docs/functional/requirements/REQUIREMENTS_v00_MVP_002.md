# MVP Requirements v00 — Tool Parity Detailing

## PURPOSE
- Clarify and lock the full Codex tool surface for the production-ready MVP, enumerating every required tool, description, and interface signature to eliminate parity gaps. Builds on `REQUIREMENTS_v00_MVP_001.md`.

## SCOPE REMINDERS
- Python 3.12 only; Linux target.
- OpenAI-only LLM; privative license.
- Full host-access tools with warnings (no confirmations by default).
- Artifacts under `artifacts/<run_id>/`; JSON logs to stdout + `logs/codex.log`.
- Poetry packaging; per-file coverage ≥80%; ruff, strict mypy, pytest + coverage gate.

## SHARED TOOL CONTRACT
- Base interface: tools expose `name: str`, `description: str`, and `run(*args, **kwargs) -> ToolResult`.
- `ToolResult`: `{ output: str, success: bool, metadata: dict | None }`.
- All tools must log invocation + args (with secret redaction) and include return code / status in metadata when applicable.

## TOOL CATALOG (Paritizing Original Codex)

### Shell Tool
- **Name:** `shell`
- **Purpose:** Execute shell commands inside the workspace.
- **Signature:** `run(command: str, cwd: str | None = None, timeout: int | None = None) -> ToolResult`
- **Notes:** Warn on risky patterns (`rm -rf`, destructive git). Truncate very long output; include `returncode` in metadata.

### Filesystem Tools
- **Name:** `fs_read`
  - **Purpose:** Read a text file.
  - **Signature:** `run(path: str, encoding: str = "utf-8") -> ToolResult`
  - **Notes:** Guard path to workspace; reject binary (heuristic); metadata includes `bytes_read`.
- **Name:** `fs_write`
  - **Purpose:** Write or overwrite a text file.
  - **Signature:** `run(path: str, content: str, encoding: str = "utf-8", append: bool = False) -> ToolResult`
  - **Notes:** Warn on overwrite; support append; binary rejection; metadata includes `bytes_written`, `mode`.
- **Name:** `fs_list`
  - **Purpose:** List directory entries.
  - **Signature:** `run(path: str) -> ToolResult`
  - **Notes:** Path normalization; metadata includes `entries` (list) and `count`.
- **Name:** `fs_mkdir`
  - **Purpose:** Create a directory (optionally parents).
  - **Signature:** `run(path: str, parents: bool = True, exist_ok: bool = True) -> ToolResult`
  - **Notes:** Workspace guard; metadata includes `created` bool.
- **Name:** `fs_remove`
  - **Purpose:** Remove file or directory.
  - **Signature:** `run(path: str, recursive: bool = False, force: bool = False) -> ToolResult`
  - **Notes:** Emit warning for deletes; guard against workspace escape; metadata includes `removed` bool.
- **Name:** `fs_glob`
  - **Purpose:** Glob-matching files relative to workspace.
  - **Signature:** `run(pattern: str) -> ToolResult`
  - **Notes:** Return matched relative paths in metadata `matches`.

### Git Tools
- **Name:** `git_status`
  - **Purpose:** Show repository status.
  - **Signature:** `run(repo_path: str = ".") -> ToolResult`
- **Name:** `git_diff`
  - **Purpose:** Show diff against HEAD or provided revs.
  - **Signature:** `run(repo_path: str = ".", rev: str | None = None, paths: list[str] | None = None) -> ToolResult`
- **Name:** `git_show`
  - **Purpose:** Show object (commit/tree/blob) content.
  - **Signature:** `run(repo_path: str = ".", ref: str) -> ToolResult`
- **Name:** `git_apply_patch`
  - **Purpose:** Apply unified diff patch.
  - **Signature:** `run(repo_path: str = ".", patch: str, check: bool = True) -> ToolResult`
  - **Notes:** Validate patch format; include `returncode`.
- **Name:** `git_branches`
  - **Purpose:** List branches.
  - **Signature:** `run(repo_path: str = ".", all: bool = False) -> ToolResult`
- **Name:** `git_commit` (optional/warn-only)
  - **Purpose:** Create commit when explicitly enabled.
  - **Signature:** `run(repo_path: str = ".", message: str, all: bool = False) -> ToolResult`
  - **Notes:** Default behavior is to warn/log and no-op unless configuration allows commits.

### HTTP Tool
- **Name:** `http`
- **Purpose:** Perform HTTP requests (GET/POST) with headers/body handling.
- **Signature:** `run(method: str, url: str, headers: dict[str, str] | None = None, params: dict[str, str] | None = None, json: dict | None = None, data: str | bytes | None = None, timeout: int = 20) -> ToolResult`
- **Notes:** TLS verify on; size/time limits; truncates large bodies; metadata includes `status_code`, `headers` (truncated), `elapsed_ms`.

### Search Tool
- **Name:** `search`
- **Purpose:** Web search returning ranked snippets/links.
- **Signature:** `run(query: str, num_results: int = 5) -> ToolResult`
- **Notes:** Pluggable backend; rate-limit handling; metadata includes list of `{title, url, snippet}`.

### Summarize / Analysis Tool
- **Name:** `summarize`
  - **Purpose:** Summarize provided text or file content.
  - **Signature:** `run(text: str, max_tokens: int = 512, style: str | None = None) -> ToolResult`
- **Name:** `analyze`
  - **Purpose:** Lightweight analysis/stats (e.g., word count, reading time) over text or file.
  - **Signature:** `run(text: str) -> ToolResult`
- **Notes:** Uses LLM prompts with chunk/merge for long inputs; file inputs must be read via fs tools then passed.

### Workflow Loader/Runner Helpers (supporting tool use)
- **Name:** `workflow_validate`
  - **Purpose:** Validate workflow file against schema v1.
  - **Signature:** `run(path: str) -> ToolResult`
- **Name:** `workflow_run`
  - **Purpose:** Execute a workflow definition using the tool registry and LLM.
  - **Signature:** `run(path: str, params: dict[str, str] | None = None) -> ToolResult`

## ACCEPTANCE CRITERIA FOR MVP_002
- All tools above are implemented with signatures matching this catalog, registered in the tool registry, and usable by the LangGraph agent and workflow compiler.
- Safety: path normalization for fs/git; warnings for destructive shell/fs/git ops; secret redaction in logs; timeouts/truncation for shell/http.
- Logging: each tool emits JSON log line with name, args (safe), success flag, and metadata.
- Tests: unit tests per tool covering happy/error paths, warnings, redaction; integration tests ensure registry wiring and workflow execution uses these tools.
- Documentation: README/ARCHITECTURE updated to reference the full tool set and interfaces.
