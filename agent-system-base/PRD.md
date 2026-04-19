# PRD: Personal AI Execution Stack

**Document type:** Product requirements — dual layer (AS-BUILT + TARGET)  
**Owner:** Miguel González  
**Canonical blueprint repo:** `agent-system-base` (typically `~/agents/agent-system-base`)  
**Runtime mirror:** `~/agents/agent-services` (synced by `init.sh`)  
**Claude global layer:** `~/.claude` (orchestrator, agents, schemas — synced by `init.sh`)

---

## 0. Drift notice (read first)

This PRD has **two layers**:

| Layer | Purpose | Rule |
|--------|---------|------|
| **AS-BUILT** | What the code and filesystem do today | **Source of truth** for operators, automation, and specs |
| **TARGET** | Planned UI/API/product evolution | **Not implemented** until shipped; do not treat as live contracts |

**If AS-BUILT and TARGET conflict, AS-BUILT wins** until you deliberately change the implementation.

Downstream tools (Execution Spec Gate, Operator, Strategist) must **execute against AS-BUILT** only.

---

## 1. System identity

**What (AS-BUILT):** A **local, human-in-the-loop** execution stack: **SQLite** holds projects, tasks, runs, and AI **proposals**; a **FastAPI** dashboard exposes read APIs and manual completion; **two workers** bridge `tasks.json` → SQLite and **claim one task** per invocation to prepare or run execution; **Claude** global config (`~/.claude`) holds orchestrator, agent JSON, skills, and the global task board file.

**Who:** Single operator (local machine).

**Why:** Separate **intent** (tasks), **execution history** (runs), and **governed mutations** (proposals → approve), with an auditable trail.

**TARGET outcome:** Single authoritative **React + Tailwind** dashboard, stricter project-scoped APIs, and removal of the HTML UI — see **§14**.

---

## 2. Architecture

### 2.1 AS-BUILT

| Component | Role | Location / notes |
|-----------|------|------------------|
| **Blueprint repo** | Version-controlled system design + code | `agent-system-base/` |
| **`init.sh`** | Sync: `orchestrator/`, `agents/`, `schemas/` → `~/.claude/`; `system/`, `workers/`, `config/` → `~/agents/agent-services/` | Repo root |
| **SQLite** | System of record | `system/db/database.sqlite` (path configured in `system/services/db.py`) |
| **Migrations** | Schema evolution | `system/db/migrations/*.sql` |
| **Service layer** | All DB writes go through services | `system/services/*.py` |
| **FastAPI dashboard** | HTTP API + serves UI | `system/dashboard/server.py` |
| **Primary UI** | Single-page dashboard | `system/dashboard/index.html` (served at `GET /`) |
| **Secondary UI** | Vite/React app (build under `ui/dist/`) | `system/dashboard/ui/` — **not** wired as `GET /` today |
| **Execution worker** | Claim **one** pending task; manual = create run + `pending_input` + prompt; AI = API execution | `system/services/task_worker.py` |
| **Import worker** | `tasks.json` → SQLite tasks | `workers/task_worker.py` → synced to `~/agents/agent-services/workers/` |
| **Supporting workers** | e.g. decision review, optional Gmail triage | `workers/*.py` |
| **`install.sh`** | Optional **cron** (import worker schedule, decision reviewer) | Synced to `agent-services/` |
| **Claude OS** | Orchestrator, plans, agent definitions | `~/.claude/` after sync |
| **Cursor** | Editor-local skills | `~/.cursor/skills-cursor/` (and project metadata under `~/.cursor/projects/`) |

**Python dependencies:** `system/services/requirements-worker.txt` documents **Anthropic** for AI execution mode; the dashboard requires **FastAPI** and **uvicorn** (ensure your environment installs them).

**Default dashboard URL:** `http://127.0.0.1:8765` (see `server.py`).

### 2.2 TARGET

- **Frontend:** One **React + Tailwind** app replaces `index.html` as the only operator UI.
- **APIs:** Project-scoped run/task listing, optional blueprint and PDF export — **specified in §14, not live today.**

---

## 3. Data model (AS-BUILT ONLY)

Derived from migrations `m001`–`m007` and service-layer enums.

### 3.1 `schema_version`

| Column | Description |
|--------|-------------|
| `migration_name` | TEXT PRIMARY KEY — migration file name |
| `applied_at` | TEXT — when applied |

### 3.2 `projects`

| Column | Required | Description |
|--------|----------|-------------|
| `id` | auto | Primary key |
| `name` | yes | Display name |
| `slug` | yes | Unique slug |
| `root_path` | no | Optional on-disk root (m002) |
| `created_at` | yes | |
| `updated_at` | yes | |

### 3.3 `tasks`

| Column | Required | Description |
|--------|----------|-------------|
| `id` | auto | Primary key |
| `project_id` | yes | FK → `projects.id` |
| `title` | yes | |
| `description` | no | |
| `status` | yes | `pending`, `queued`, `in_progress`, `blocked`, `done`, `cancelled`, `failed` |
| `priority` | yes | `low`, `normal`, `high`, `urgent` |
| `type` | yes | `feature`, `bug`, `chore`, `research`, `maintenance`, `other` |
| `source` | yes | `manual`, `cron`, `api`, `import`, `orchestrator`, `other`, `project_import` |
| `created_at` | yes | |
| `updated_at` | yes | |

### 3.4 `runs`

| Column | Required | Description |
|--------|----------|-------------|
| `id` | auto | Primary key |
| `task_id` | yes | FK → `tasks.id` |
| `mode` | yes | `manual`, `ai` |
| `status` | yes | `pending`, `pending_input`, `running`, `success`, `failed`, `cancelled` |
| `input_prompt` | no* | Set when transitioning to `pending_input` |
| `output` | no | Result text (serialized if non-string) |
| `agent` | legacy | Legacy column; not written by new code paths |
| `started_at` | yes | |
| `completed_at` | no | Set when terminal |
| `error_message` | no | Required in services when status is `failed` |

\*Service layer: `input_prompt` may only be set when moving to `pending_input`.

**Transitions:** Enforced in `run_service.update_run` (no illegal jumps; terminal runs immutable).

### 3.5 `proposed_actions`

| Column | Description |
|--------|-------------|
| `id` | Primary key |
| `type` | `create_task`, `update_task`, `other` |
| `payload` | JSON string (arguments) |
| `status` | `pending`, `approved`, `rejected` |
| `created_by` | Optional |
| `created_at` | |
| `reviewed_at` | |
| `review_note` | |

**Approve behavior:** `create_task` → `task_service.create_task(...)`; `update_task` → `task_service.update_status(...)`; `other` → audit only, no task mutation.

### 3.6 `decisions` / `memory` (m003)

Append-only / key-value tables used by the broader system; not part of the core task/run loop but **exist in AS-BUILT schema**.

---

## 4. Core workflows (AS-BUILT)

### 4.1 Manual task execution (primary)

1. Task exists in SQLite with `status = pending` (origin: import, API, manual create, approved proposal, etc.).
2. Operator runs **`system/services/task_worker.py`** (default `--mode manual`, optional `--project-id`).
3. Worker may recover stale `in_progress` tasks and orphan `running` runs.
4. Worker **claims** one `pending` task → sets **`in_progress`**.
5. Worker **`create_run`** (manual) → run starts **`pending`**, then **`pending_input`** with **`input_prompt`** set; prints `READY task_id=… run_id=…`; **exits**.
6. Operator executes prompt **outside** the app (Claude/Cursor).
7. Operator **`POST /api/tasks/{task_id}/complete`** with **plain text** body = output.
8. If a `pending_input` run exists: **`complete_manual_run`**: run → `running`, task → **`done`**, run → **`success`** (that ordering is enforced in services).

**Stuck states:** No submission leaves run in `pending_input` and task `in_progress`. No pending tasks → worker exits quietly.

### 4.2 AI task execution (same worker, different mode)

`--mode ai`: worker claims one task and executes via Claude Messages API path (`claude_execution`); run/task updated without a `pending_input` copy-paste loop.

### 4.3 Import from `tasks.json`

**`workers/task_worker.py`:** Reads `~/.claude/tasks.json` (and per-project boards per `config/projects_index.json`), imports into SQLite as appropriate. Optional **cron** via `install.sh`.

### 4.4 Proposal review

1. Proposal row `status = pending`.
2. Operator uses dashboard APIs to **approve** or **reject**.
3. On approve, service executes typed side effects (see §3.5).

---

## 5. Business rules (AS-BUILT)

- **Tasks** = intent queue; **runs** = execution attempts ( **1:N** allowed).
- **One task claimed per execution-worker invocation** (not parallel workers in one process).
- **Run created before external execution** in the normal manual path (`pending` → `pending_input` with prompt).
- **`pending_input`** means: system prepared prompt; human must act.
- **AI agents** must not write tasks directly; they stage **`proposed_actions`** (see `AGENTS.md`). Tasks may still enter via **import, API, manual creation, orchestrator**, etc.
- **Manual completion** resolves run **via task id**; server picks a **`pending_input`** run for that task if present.

---

## 6. Constraints (AS-BUILT)

- **No ORM:** raw SQL via `sqlite3` centralized in `db.py`; services own queries.
- **Service layer** between HTTP and DB for dashboard and workers.
- **SQLite** is the execution source of truth; `tasks.json` is an **import/input** surface, not the runtime queue (see `WORKFLOW.md`).
- **Localhost operator:** no multi-user auth in dashboard.
- **External execution** in manual mode: the app prepares and records; it does not run the LLM for you.

---

## 7. API contracts (AS-BUILT ONLY)

Base: **`http://127.0.0.1:8765`**  
OpenAPI: **disabled** (`docs_url=None`).

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard HTML (`index.html`) |
| GET | `/api/projects` | List projects |
| GET | `/api/tasks` | Query: `project_id`, `status` (optional) |
| GET | `/api/tasks/{task_id}` | Single task |
| GET | `/api/tasks/{task_id}/runs` | Runs for task |
| GET | `/api/runs` | **All** runs (aggregated), newest first, **max 500** — **no `project_id` filter** |
| POST | `/api/tasks/{task_id}/complete` | Body: **plain string** = output. Prefers `pending_input` run; else creates run and completes. |
| GET | `/api/proposed-actions` | Pending proposals |
| GET | `/api/proposed-actions/all` | All proposals |
| POST | `/api/proposed-actions/{action_id}/approve` | Approve → execute |
| POST | `/api/proposed-actions/{action_id}/reject` | Body: optional plain-string note |

**TARGET (not implemented):** `POST /runs/{id}/complete`, `GET /runs?project_id=`, blueprint endpoints, PDF export — **§14**.

---

## 8. File structure (AS-BUILT)

```
agent-system-base/                 # Blueprint repo
├── init.sh
├── install.sh
├── CLAUDE.md
├── AGENTS.md
├── WORKFLOW.md
├── PRD.md                         # This document
├── config/
│   ├── .env.template
│   └── projects_index.json
├── schemas/
├── orchestrator/                  # python -m orchestrator (see __main__.py)
├── agents/
│   ├── *.json
│   └── plans/
├── system/
│   ├── db/
│   │   ├── database.sqlite
│   │   └── migrations/
│   ├── services/
│   └── dashboard/
│       ├── server.py
│       ├── index.html
│       └── ui/
└── workers/

~/.claude/                         # After init.sh — NOT a full copy of system/
├── orchestrator/
├── agents/
├── schemas/
├── tasks.json
├── memory/
├── hooks/
├── skills/
└── …

~/agents/agent-services/           # After init.sh — runtime mirror
├── system/                        # Full system tree
├── workers/
├── config/
├── state/
└── logs/
```

---

## 9. Validation and auth (AS-BUILT)

- **Validation:** Service layer (status enums, illegal run transitions, proposal typing).
- **Auth:** None (single operator, local).
- **Task complete:** Rejects if task not `pending` or `in_progress`.

---

## 10. Success conditions

- Operator can run **manual loop**: worker → `pending_input` → external run → **`POST /api/tasks/{id}/complete`** → task `done`, run `success`.
- Proposals are reviewable and auditable.
- Run history exists per task via **`GET /api/tasks/{id}/runs`**.

---

## 11. Failure conditions

- Downstream specs assume **TARGET** endpoints as live (**drift**).
- **Mixed project context** in UI because **`GET /api/runs`** is global (AS-BUILT).
- Bypassing services and writing SQLite directly.
- Multiple concurrent **execution** workers without coordination (SQLite locking / logical races).

---

## 12. Open assumptions

- Single-operator model remains valid.
- SQLite scale remains sufficient.
- Manual execution remains the default day-to-day path.

---

## 13. MVP scope

**AS-BUILT MVP (already largely present):** tasks, runs, proposals, HTML dashboard, workers, Claude sync.

**TARGET MVP (§14):** React-only UI, project-scoped APIs, optional blueprint/PDF.

---

## 14. TARGET evolution (NOT AS-BUILT)

> Everything in this section is **design intent**. Implementations must update **§7** and **§3** when shipped.

### 14.1 Dashboard migration — React + Tailwind

**Objective:** Replace `index.html` with a **single** React + Tailwind app; delete duplicate UI logic; align 1:1 with **future** backend contracts.

**Target routes (illustrative):**

- `/projects`, `/projects/:slug`, optional global `/tasks`, `/runs`

**Target workspace:** `/projects/:slug` with tabs (Overview, Tasks, Runs default, Blueprint).

**Target load order:** Resolve project by slug → `project_id` → then fetch scoped tasks/runs (requires **new or extended APIs**).

**Runs UI:** Three panels (list / prompt / output); default filter **`pending_input`**.

**Target completion API (optional redesign):** e.g. `POST /runs/{id}/complete` **or** keep task-centric completion — **decide at implementation time** and update AS-BUILT.

**Target extras:** Blueprint tab, PDF export — **require** blueprint data model and endpoints **not present** in AS-BUILT.

**Build order (suggested):** projects list → workspace shell → runs tab + submit → tasks tab → blueprint → remove HTML.

---

## 15. Operational commands (AS-BUILT)

```bash
# Sync blueprint → ~/.claude + ~/agents/agent-services
bash ~/agents/agent-system-base/init.sh /path/to/active-project

# Dashboard (from synced runtime)
cd ~/agents/agent-services && python3 system/dashboard/server.py

# Import worker (tasks.json → SQLite)
cd ~/agents/agent-services && python3 workers/task_worker.py

# Execution worker — prepare manual run (one task)
cd ~/agents/agent-services && python3 system/services/task_worker.py --mode manual

# Optional: AI execution mode (requires API key + deps)
cd ~/agents/agent-services && python3 system/services/task_worker.py --mode ai

# Optional cron
bash ~/agents/agent-services/install.sh

# Orchestrator (from global Claude dir)
cd ~/.claude && python3 -m orchestrator --runs-dir /path/to/project/runs/ephemeral --plan swarm_research --goal "..." --mode simulate
```

**Plain-language walkthrough:** See **`OPERATOR_GUIDE.md`** in this repo for step-by-step explanations, prerequisites, and troubleshooting.

---

## Document control

| Version | Date | Notes |
|---------|------|--------|
| 1.0 | 2026-04-02 | Initial official dual-layer PRD (AS-BUILT aligned to repo + runtime) |

**Maintainers:** Update **§0–§13** whenever behavior or schema changes; move shipped features out of **§14** into AS-BUILT sections.
