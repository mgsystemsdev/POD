# The SQLite Database (Operational Mirror)

## System purpose

The SQLite database is the **operational mirror** (Layer 3) and **control plane**: it turns authored files into queryable state for the dashboard and workers. **Files** remain authored truth; the **database** is approved operational reality—reducing drift and keeping a human gate for agentic writes.

---

## Inputs

| Input | Description |
| :--- | :--- |
| **Knowledge bundle** (`.claude/context/`) | `project.md`, `tasks.json`, `session.md`, `decisions.md`, etc. |
| **Sync CLI** (`agents push`) | One-way flow from project files into the database. |
| **Internal agent requests** | Proposals landing in `proposed_actions` for human review. |
| **Dashboard API** | Operator actions: task done, approve proposed action, etc. |

---

## Outputs

| Output | Description |
| :--- | :--- |
| **10-tab dashboard** | Live state at `http://localhost:8765`. |
| **Execution prompts** | Workers pull blueprint, decisions, session history for Claude Code / Cursor. |
| **Health signals** | `agents status`, Health tab: connectivity, integrity, paths. |
| **Run history** | Auditable task runs (success/failure, logs). |

---

## Key entities and schema

Single SQLite file (typically `database.sqlite`). Core tables:

| Table | Core fields | Purpose |
| :--- | :--- | :--- |
| `projects` | `id`, `name`, `slug`, `root_path` | Registered projects. |
| `tasks` | `id`, `project_id`, `title`, `description`, `status`, `priority`, `requirement_ref`, `success_criteria`, `failure_behavior`, `depends_on`, `correlation_id` | Atomic work units; align with PRD. |
| `runs` | `id`, `task_id`, `status`, `output`, `created_at` | Execution attempts (`pending_input`, `running`, `success`, `failure`). |
| `blueprints` | `id`, `project_id`, `type`, `content`, `version`, `updated_at` | Mirror of `project.md` for UI. |
| `decisions` | `id`, `project_id`, `title`, `content`, `review_date`, `created_at` | Architectural memory. |
| `session_logs` | `id`, `project_id`, `session_date`, `agent`, `scope_active`, `tasks_completed`, `next_task`, `notes` | Session continuity. |
| `proposed_actions` | `id`, `project_id`, `action_type`, `payload`, `status`, `source_agent`, `impact_level`, `reversibility` | Human gate for agent writes. |
| `memory` | `id`, `project_id`, `key`, `value`, `type` | Mirrored context for prompts. |

---

## Workflow

1. **Sync (disk → DB)** — `agents push`: `sync_worker` updates blueprints / decisions / session logs from `.claude/context/*.md`; `import_worker` atomically ingests `tasks.json` → `tasks`.
2. **Proposed action gate** — Agent writes `proposed_actions` → Actions tab → approve → commit to primary tables.
3. **Task execution** — Worker claims pending task, loads blueprint + session context, creates `runs` row (`pending_input`).
4. **Completion** — After merge + human confirmation, `POST /api/tasks/{id}/complete` sets task `done` and run `success`.

---

## Constraints

- **Unidirectional truth** — Files are authoritative; DB mirrors; DB does not overwrite project files.
- **WIP limit** — One `in_progress` task per project.
- **Dashboard read-only** — Blueprints / Decisions edited on disk, not only in UI.
- **Requirement integrity** — Done only after verification gate (e.g. REQ-008) is satisfied.

---

## Edge cases

| Case | Handling |
| :--- | :--- |
| **Orphaned tasks** | Stuck `in_progress` flagged via `agents status` / worker recovery. |
| **Registration gaps** | Missing `.claude/context/` → skip + warn. |
| **Schema / path moves** | Update `projects.root_path` and `projects_index.json` together. |
| **Empty states** | Dashboard shows explicit empty messages, not blank tabs. |

---

## State handling

- **Persistence** — Local `database.sqlite`; easy backup (e.g. cron).
- **Mirroring** — DB for query/UI; files for dense agent context.
- **Session continuity** — Runs capture start/end so context reloads quickly.

---

## Failure handling

- **Loud diagnostics** — Sync/ingestion failures visible; bad `tasks.json` batch fails entirely.
- **Fail-closed** — Unknown `action_type` or invalid `task_id` → skip + log.
- **Atomic migrations** — Schema changes (e.g. M008–M013) all-or-nothing.

---

## Examples

- **Blueprint ingest** — Payload with `ingest_blueprint` → new `blueprints` row; Blueprint tab updates.
- **Proposed action** — Internal agent → Actions tab → approve → new `tasks` row as `pending`.
