# Task worker (Claude execution)

`task_worker.py` claims **one** pending task per process (`task_service.claim_next_pending`), creates a run (`run_service.create_run`), moves it **pending → running → success|failed**, and sets the task **done** or **blocked**. Assistant text is stored in `runs.agent` on success (via `run_service.update_run(..., output=...)`).

## Dependencies

```bash
pip install -r requirements-worker.txt
```

Requires **`ANTHROPIC_API_KEY`** in the environment.

## Environment

| Variable | Meaning |
|----------|---------|
| `ANTHROPIC_API_KEY` | Required for API calls |
| `ANTHROPIC_MODEL` | Default model (built-in default if unset) |
| `CLAUDE_MAX_TOKENS` | Max output tokens |
| `CLAUDE_TIMEOUT_S` | Per-request timeout (seconds) |
| `CLAUDE_MAX_RETRIES` | Retries for transient API errors (429, 5xx, timeouts) |

## Run

From `system/services` (so imports resolve):

```bash
export ANTHROPIC_API_KEY=...
python3 -m task_worker --project-id <PROJECT_ID>
```

One invocation processes **at most one** task for that project.

## Architecture

- **No** direct `sqlite3` / `db` in `task_worker.py`; only `task_service`, `run_service`, `context_loader`, `claude_prompts`, `claude_execution`.
- Project context comes from `context_loader.load_project_context(project_id=...)`.
- Failures: run ends **failed** with `error_message`; task **blocked**.
