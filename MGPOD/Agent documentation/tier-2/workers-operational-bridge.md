# The Workers layer (Operational Bridge)

## System purpose

The Workers layer is the **operational bridge** (Layer 3): it automates moving authored knowledge from `.claude/context/` into SQLite, prepares tasks for execution, injects architectural context into prompts, and runs scheduled hygiene (e.g. decision reviews).

---

## Inputs

| Input | Description |
| :--- | :--- |
| **Project context** | Valid `.claude/context/` bundle: `project.md`, `tasks.json`, `session.md`, `decisions.md`. |
| **Database** | Current `tasks`, `projects`, `runs` for dependencies and state. |
| **Environment** | `ANTHROPIC_API_KEY` (for execution prompts), `DATABASE_URL`. |
| **Execution evidence** | Terminal output, test logs for completion handling. |

---

## Outputs

| Output | Description |
| :--- | :--- |
| **Database mutations** | Atomic inserts/updates to the operational mirror. |
| **Enriched prompts** | Self-contained instructions for Claude Code or Cursor. |
| **Logs** | e.g. `task_worker.log`, `dashboard.log`. |
| **Run history** | New `runs` rows with success/failure. |

---

## Key entities and schema

| Entity | Field / aspect | Rule |
| :--- | :--- | :--- |
| **Task (import)** | `action_type` | One of `ingest_task`, `ingest_blueprint`, `ingest_decision`, `ingest_session_log`. |
| **Run** | `status` | `pending_input`, `running`, `success`, or `failure`. |
| **Blueprint** | `version` | Incremented on each `project.md` sync. |
| **Decision** | `review_date` | e.g. UTC now + 30 days for review worker. |

---

## Workflow

### 1. Sync worker (`agents push`)

1. Read `.claude/context/*.md`.
2. Parse `project.md` (blueprint), `decisions.md`, `session.md`.
3. One-way sync disk → SQLite for mirror tables.

### 2. Import worker (`task_worker.py --import`)

1. Load `tasks.json`.
2. Validate `id`, `sqlite_project_slug`, `success_criteria` (and related rules).
3. **Atomic** import—all tasks or none.

### 3. Execution worker (`task_worker.py --execute`)

1. Pick highest-priority pending task with `depends_on` satisfied.
2. Load latest blueprint, recent decisions, latest session log.
3. Build self-contained prompt (description, constraints, failure behavior).
4. Set task `in_progress`; create `run` with `pending_input`.

### 4. Decision reviewer (`decision_reviewer.py`)

1. Find `decisions` where `review_date <= today`.
2. Flag as `pending_review` in the dashboard.

---

## Constraints

- **Unidirectional truth** — Workers never overwrite `.claude/context/`; flow is disk → DB.
- **WIP limit** — One `in_progress` task per project in execution worker.
- **Manual proof gate** — Automate only after **three** successful manual runs of the same workflow.
- **Plain English** — Operator-facing worker copy in paragraphs, not opaque jargon.

---

## Edge cases

| Case | Behavior |
| :--- | :--- |
| **Missing API key** | Execution worker stops; loud failure / Health tab. |
| **Duplicate tasks** | Dedupe on `(title, source='import')` where implemented. |
| **PRD vs code drift** | Stop execution; prompt user to sync with Architect / `project.md`. |

---

## State handling

- **Operational context** — `database.sqlite` mirror.
- **Baton files** — `analysis.md`, `plan.md`, `handoff.md` pass state between tools without full re-reads.

---

## Failure handling

- **Fail loudly** — No silent failures; errors logged and surfaced (e.g. red dashboard alerts).
- **Correction loop** — Failed tasks produce diagnostics and a “fix prompt” for retry.

---

## Examples

- **`agents push`** — Tasks from `tasks.json` appear in `tasks`; `project.md` → `blueprints`; dashboard refreshes.
- **Execution claims `TASK-042`** — Status `in_progress`, new `run`, ~1.5k-token prompt with PRD + decisions.
