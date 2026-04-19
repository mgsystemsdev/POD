# The Dashboard and FastAPI backend

## System purpose

The Dashboard and FastAPI backend serve as the **Control Plane** (Layer 3) and **Visibility Layer** (Layer 5) of the Personal Developer OS. They provide an operational mirror of authored project knowledge and a human-governed command center for agentic execution—so project state stays visible, reviewable, and auditable across tools and sessions.

---

## Inputs

| Input | Description |
| :--- | :--- |
| **Operational mirror (SQLite)** | Runtime source of truth: projects, tasks, runs, blueprints, decisions, session logs, proposed actions. |
| **Knowledge bundle** (`.claude/context/`) | Authored Markdown and JSON, synced via `agents push`. |
| **Agent / CLI requests** | API calls from thinking tools (e.g. ChatGPT) or local workers. |
| **Environment variables** | `DATABASE_URL`, `LOG_DIR`, `ANTHROPIC_API_KEY`. |

---

## Outputs

| Output | Description |
| :--- | :--- |
| **Monolithic UI** (`index.html`) | Single-file vanilla JS at `http://localhost:8765`: project-scoped tabs and global controls. |
| **JSON API** | REST endpoints for CRUD on project entities. |
| **Server-Sent Events (SSE)** | Real-time streams for logs and the `proposed_actions` approval queue. |
| **System health** | Green / yellow / red signals for DB connectivity, workers, project path validity. |

---

## Key entities and schema

| Entity | SQLite table | Core fields |
| :--- | :--- | :--- |
| **Project** | `projects` | `id`, `name`, `slug`, `root_path` |
| **Task** | `tasks` | `id`, `title`, `description`, `status`, `priority`, `requirement_ref`, `success_criteria`, `failure_behavior` |
| **Blueprint** | `blueprints` | `id`, `project_id`, `type` (prd/blueprint), `content`, `version` |
| **Decision** | `decisions` | `id`, `project_id`, `title`, `content`, `created_at` |
| **Session log** | `session_logs` | `id`, `project_id`, `session_date`, `tasks_completed`, `notes` |
| **Proposed action** | `proposed_actions` | `id`, `project_id`, `action_type`, `payload`, `status` (pending/approved/rejected) |

---

## Workflow

1. **Project selection** — Sidebar selection updates `project_id` in the UI.
2. **Observe mode** — Dashboard loads scoped APIs (e.g. `GET /api/projects/{id}/tasks`) and renders tabs across groups (Work, Knowledge, System).
3. **Control mode (gatehouse)** — Internal agents use `proposed_action_service`; changes stage in the **Actions** tab.
4. **Human approval** — Operator reviews `action_payload`; `POST /api/proposed-actions/{id}/approve` commits to operational tables.
5. **Execution sync** — Workers complete work; `POST /api/tasks/{id}/complete` updates task status and run history.
6. **State mirroring** — After session close, `agents push` reconciles disk with SQLite.

---

## Constraints

- **Read-only authored data** — Blueprints and Decisions are read-only in the UI; edits come from files on disk.
- **Unidirectional sync** — Disk → SQLite only; the database must not overwrite authored Markdown.
- **WIP limit** — Exactly one task per project in `in_progress`.
- **Atomic ingestion** — Any error in a `tasks.json` batch fails the whole import.

---

## Edge cases

| Case | Behavior |
| :--- | :--- |
| **Missing `ANTHROPIC_API_KEY`** | Red alert in Health; `task_worker` blocked from autonomous runs. |
| **Registration gap** | Project path lacks `.claude/context/` → warning; sync skipped. |
| **Stale runtime** | If `init.sh` / sync is old, flag mismatch between blueprint and mirror. |
| **Empty states** | Tabs show explicit messages (e.g. “Requirement not found”, “No decisions logged”), not blank screens. |

---

## State handling

- **Persistence** — Typically `database.sqlite` under `agent-system-base/system/db/` (or as configured).
- **Portability** — `db.py` resolves path via `Path.home()` / `Path(__file__)` for Mac and VPS.
- **Refresh** — SSE for high-churn tabs (Actions, CLI); other tabs may use manual refresh.

---

## Failure handling

- **Loud diagnostics** — HTTP 400 / 401 / 404 with plain-English bodies.
- **Rollback** — Failed proposed actions or completions block merge until resolved.
- **Health** — `/api/health` checks table counts and processes; alerts in the dashboard strip.

---

## Examples

- **Approve proposed action** — User clicks Approve on `create_task` for Project 4 → `POST /api/proposed-actions/{action_id}/approve` → new `tasks` row, action moves to “Recently Decided”.
- **Agent lookup** — `GET /api/projects/by-slug/dmrb` → JSON with `id`, `name`, `root_path`.

---

## PDOS context (dashboard scope)

The Personal Developer Operating System is a structured, context-driven layer from ideas to approved, traceable execution—reducing context loss and keeping continuity across Claude Code, Cursor, and sessions.

### Additional inputs

- **Global memory** (`~/.claude/memory/`) — `user.md`, `preferences.md`, global decisions.
- **Project context** (`.claude/context/`) — `project.md`, `tasks.json`, `session.md`, `decisions.md`.
- **Dashboard docs** (`.claude/docs/`) — Tab specs, e.g. `00-overview.md` … `10-health.md`.
- **Codebase** — Local filesystem and terminal (Layer 4).

### Additional outputs

- **Operational state** — SQLite mirror of authored files.
- **Tool adapters** — `CLAUDE.md` (system + codebase sections); `.cursor/rules/00-context.mdc`.
- **Execution artifacts** — Task branches, PRs on GitHub.
- **Continuity** — Updates to `session.md`, `decisions.md`.

### PDOS workflow (summary)

1. **Onboarding** — `agents init` scaffolds context, tab docs, adapters, registry + DB.
2. **Synchronization** — `agents push` mirrors disk → SQLite.
3. **Execution loop** — Isolated branch → Step 0 analysis → Plan mode → surgical implementation → verification → PR → merge → pull.

### PDOS constraints

- WIP = 1; unidirectional sync; PRs via GitHub (no casual local merge to `main`); plain-English summaries for operators; automation earned after three manual successes.

### PDOS edge cases

- Task drift → stop, Architect / PRD update.
- Budget depletion → Gemini CLI + Cursor fallback patterns.
- Dirty Git → Operator blocks until clean, updated `main`.

### PDOS failure handling

- Fail loudly; correction loop on verification failure; major structural failure → documented reset toward design / Architect stage.

### PDOS examples

- `agents init my-project` → full `.claude/context/`, `.claude/docs/`, registry entry, initial DB sync.
- Approve `TASK-022` → branch `feature/TASK-022`, analysis, plan, changes, evidence, GitHub PR.
