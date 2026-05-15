# Agents monorepo — architecture map

This repository is a **multi-root workspace**, not a single deployable app with one `src/` tree. Use this document to map folders to **domain / application / infrastructure** concerns without breaking the **blueprints → global → runtime** sync model.

## Three surfaces (operational)

| Location | Role |
|----------|------|
| `agent-system-base/` | **Blueprints** — edit source of truth here. |
| `~/.claude/` | **Global Claude layer** — synced from `orchestrator/`, `agents/`, `schemas/`, `.claude/` via `init.sh`. |
| `~/agents/agent-services/` | **Runtime** — synced from `workers/`, `system/`, `config/`; crons and secrets live here. |

Root **Dockerfile** builds from `agent-system-base/` and runs `system/dashboard/server.py` (not `agent-services/`).

## Layer mapping (conceptual)

### Domain (contracts and definitions)

- `agent-system-base/agents/` — agent JSON definitions paired with skills.
- `agent-system-base/schemas/` — JSON schemas (e.g. `agent_output_v2`).
- `MGPOD/Official agents/` — canonical prompts and knowledge for the MGPOD library.
- `MGPOD/Legacy agents/` — **archived** prompts/knowledge; still referenced by docs and some official paths — do not delete.

### Application (use cases and orchestration)

- `agent-system-base/orchestrator/` — plan execution, CLI entrypoints.
- `agent-system-base/workers/` — import/cron entrypoints (e.g. `tasks.json` → SQLite).
- `agent-system-base/system/services/` — task/run/proposal services, execution worker, tests alongside modules.

### Infrastructure (I/O, persistence, ops UI)

- `agent-system-base/system/dashboard/` — FastAPI server and UI bundle.
- `agent-system-base/system/db/` — SQLite schema and migrations.
- `agent-system-base/system/scripts/` — maintenance and audit scripts.
- `agent-system-base/system/audit/`, `system/export/` — runtime-adjacent directories.
- `agent-system-base/config/` — env templates, `projects_index.json`, etc.
- Repo root `Dockerfile`, `railway.toml` — deployment wiring.

## Related docs

- System behavior and workers: `agent-system-base/CLAUDE.md`, `agent-system-base/OPERATOR_GUIDE.md`, `agent-system-base/docs/system_contract.md`.
- Historical audits: `docs/audits/`.
- Archived execution-plan artifact (not the `~/.claude` task queue): [`docs/plans/execution-plan-claude-worker.json`](plans/execution-plan-claude-worker.json).

## Naming note: two `task_worker.py` files

- `workers/task_worker.py` — **import worker** (`tasks.json` → SQLite).
- `system/services/task_worker.py` — **execution worker** (claims one DB task, manual or AI).

## Optional future refactors

Splitting `system/services/` into physical `domain/` vs `application/` subpackages is **high churn**; defer until static analysis and boundaries justify it.
