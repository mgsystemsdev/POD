# Operator guide — using the personal AI execution stack

This document explains **in plain language** how the system fits together and how to run the commands listed in **PRD §15 (Operational commands)**. It is meant for **day-to-day use**, not for product planning (use the PRD for schema and “AS-BUILT vs TARGET” rules).

---

## 1. What you actually have (mental model)

You maintain **three different places** on disk:

| Place | Role |
|--------|------|
| **`~/agents/agent-system-base`** | **Blueprint** — version-controlled source of truth for code you edit and commit. |
| **`~/agents/agent-services`** | **Runtime** — a **copy** of workers, dashboard, and `system/` code, produced by `init.sh`. Cron and daily commands usually run **here**. |
| **`~/.claude`** | **Global Claude layer** — orchestrator, agent definitions, plans, schemas, and the file **`tasks.json`** (a human/assistant-friendly task list). |

The **database** that powers the dashboard and the “real” execution queue is a **single SQLite file** whose path is set in **`system/services/db.py`** (`DATABASE_PATH`). On your machine it is currently the absolute path under **`agent-system-base/system/db/database.sqlite`**. Running scripts from **`~/agents/agent-services`** still uses that same `db.py` after sync, so you do **not** get two separate databases unless you change `DATABASE_PATH`.

**Important distinction — two different “task workers”:**

| Script | Full path (after sync) | What it does |
|--------|-------------------------|--------------|
| **Import worker** | `~/agents/agent-services/workers/task_worker.py` | Reads **`tasks.json`** files and **creates rows in SQLite**. It does **not** run your task in Cursor for you. |
| **Execution worker** | `~/agents/agent-services/system/services/task_worker.py` | Reads **SQLite**, **claims one** pending task, and either prepares a **manual** prompt or calls the **Anthropic API** in **AI** mode. |

If you only remember one thing: **`workers/task_worker.py` = import into DB**; **`system/services/task_worker.py` = run one task from DB**.

---

## 2. Command 1 — Sync the blueprint to your machine

```bash
bash ~/agents/agent-system-base/init.sh /path/to/active-project
```

### What it does

1. **`/path/to/active-project`** must be the root of the **project you are working on** (the repo where you want `runs/ephemeral` and optional `CLAUDE.md` seeds). Replace it with a real path, for example:
   - `~/Projects/my-app`
   - **Not** the string `path/to/active-project` literally.

2. **Copies global tooling → `~/.claude/`**  
   - **`orchestrator/`**, **`agents/`**, and **`schemas/`** from `agent-system-base` (not the `system/` tree — that goes to `agent-services` in step 3).

3. **Copies runtime → `~/agents/agent-services/`**  
   - `workers/`, `system/` (dashboard, services, DB migrations), `config/`.

4. **Prepares the active project directory**  
   - Ensures `runs/ephemeral` exists.  
   - Seeds `.claude/skills/swarm/SKILL.md` under that project.  
   - Optionally creates `CLAUDE.md` and `.env.template` in the project if missing.

5. **Global stubs**  
   - Creates empty `~/.claude/tasks.json` (`[]`) if missing.  
   - Creates `~/.claude/decisions.csv` header if missing.

### When to run it

- After you **pull** changes in `agent-system-base` and want your **runtime** and **`~/.claude`** to match.  
- When you **switch** which repo is your “active project” for orchestrator runs (you still pass that project’s path as the argument).

### What it does *not* do

- It does **not** install Python packages.  
- It does **not** install cron (use `install.sh` separately).  
- It does **not** run the dashboard or execute tasks.

---

## 3. Command 2 — Start the dashboard

```bash
cd ~/agents/agent-services && python3 system/dashboard/server.py
```

### What it does

- Starts a small **web server** (FastAPI + uvicorn) on your machine.
- Serves the **HTML dashboard** and JSON APIs for projects, tasks, and runs.

### Where to open it

- Browser: **`http://127.0.0.1:8765`** or **`http://localhost:8765`**

### Prerequisites

- Python 3 with **`fastapi`** and **`uvicorn`** installed for **that** Python.  
- If you see `ModuleNotFoundError: No module named 'uvicorn'`, install from the runtime tree:
  ```bash
  cd ~/agents/agent-services && python3 -m pip install -r system/dashboard/requirements.txt
  ```

### Typical use

- See which **projects** and **tasks** exist in SQLite.  
- Filter by status (pending, in progress, blocked, etc.).  
- After a **manual** execution run, **submit results** via the dashboard’s completion flow (the server exposes **`POST /api/tasks/{id}/complete`** — see PRD §4.1).

### Stop the server

- Press **Ctrl+C** in the terminal where it is running.

---

## 4. Command 3 — Import worker (`tasks.json` → SQLite)

```bash
cd ~/agents/agent-services && python3 workers/task_worker.py
```

### What it does

1. Reads **`~/.claude/tasks.json`** (unless you use flags like `--global-only` / `--project` — see `python3 workers/task_worker.py --help`).
2. Reads **per-project** `tasks.json` files for each **active** entry in **`~/agents/agent-services/config/projects_index.json`**.
3. For each **pending** task (not already `complete`, `blocked`, or `imported` in the JSON file), it either:
   - Handles **`log_only`** inline, or  
   - **Imports** into SQLite as a **`pending`** task (for execution later).

### Why you care

- This is how work **enters** the same database the dashboard shows.  
- Entries in **`~/.claude/tasks.json`** default to the SQLite project **`claude-global`** (“Global Claude”) **unless** you use **`sqlite_project_slug`** (or per-project `tasks.json`). See the worker docstring and your **`~/.claude/CLAUDE.md`** for conventions.

### Logs

- Append log: **`~/agents/agent-services/logs/task_worker.log`** (when not dry-run).

### Dry run

```bash
cd ~/agents/agent-services && python3 workers/task_worker.py --dry-run
```

Shows what would happen **without** writing JSON or SQLite.

### Push project markdown + tasks in one step

Writes **`.claude/project.md`** into **blueprints**; **`.claude/decisions.md`** into **decisions**; **session file** into **session_logs**; **`.claude/memory/MEMORY.md`** only into **memory** as **`mirror/memory/MEMORY.md`** (other **`memory/*.md`** stay local; legacy **`mirror_claude_*`** keys are removed). Then runs the import worker.

**Global (same registry as Command 3 — all `status: active` projects in `config/projects_index.json`, then full `task_worker.py`):**

```bash
cd ~/agents/agent-services && python3 workers/push_claude_artifacts.py
```

**Single project** (optional **`--root`** if that slug is not in the index):

```bash
cd ~/agents/agent-services && python3 workers/push_claude_artifacts.py --slug dmrb
```

The SQLite **slug** must already exist (**`POST /api/projects`** or migration). Flags: **`--dry-run`** (preview blueprint writes; skips worker), **`--no-tasks`** (only markdown → SQLite, no **`task_worker.py`**), **`--global-tasks`** (only with **`--slug`**: after **`--project`** import, also run **`task_worker.py --global-only`**). A full global run already imports **`~/.claude/tasks.json`**, so **`--global-tasks`** is redundant without **`--slug`**.

Requires the same **`system/services`** tree as the dashboard (sync from **`agent-system-base`** via **`init.sh`** if files are missing).

---

## 5. Command 4 — Execution worker, **manual** mode (recommended default)

```bash
cd ~/agents/agent-services && python3 system/services/task_worker.py --mode manual
```

### What it does (step by step)

1. **Recovery** (best effort): old **`in_progress`** tasks may be reset to **`pending`**; orphan **`running`** runs may be closed if the task is already done.  
2. **Claims exactly one** task with status **`pending`** in SQLite (highest priority, oldest first).  
3. Creates a **run** in **`manual`** mode.  
4. Builds the **prompt** from project context + task text.  
5. Writes the prompt into the run as **`pending_input`**.  
6. Prints one line such as: **`READY  task_id=…  run_id=…`** and **exits**.

### What you do next

1. Open the **dashboard**, find that task/run, and **copy the prompt** (or use whatever UI you use to read `input_prompt`).  
2. Execute the work in **Cursor**, **Claude**, or another tool.  
3. Submit the **result** through the dashboard API **`POST /api/tasks/{task_id}/complete`** (body = plain text output), so the task moves to **`done`** and the run completes.

### Optional: only one project

```bash
cd ~/agents/agent-services && python3 system/services/task_worker.py --mode manual --project-id 4
```

Use the numeric **`projects.id`** from SQLite (dashboard or DB).

### API keys

- **Manual mode does not require `ANTHROPIC_API_KEY`** for the execution worker itself.

---

## 6. Command 5 — Execution worker, **AI** mode (optional)

```bash
cd ~/agents/agent-services && python3 system/services/task_worker.py --mode ai
```

### What it does

- Same claim + run creation, but then calls the **Anthropic Messages API** via `claude_execution`, fills in output, and marks the task **done** on success.

### Prerequisites

- **`ANTHROPIC_API_KEY`** set in the environment (e.g. `~/agents/agent-services/.env` loaded before the command).  
- Dependencies as documented for the service layer (see **`system/services/requirements-worker.txt`** for the optional worker/API stack).

### Safety note

- If the key is **missing**, the worker is designed to **exit early** without claiming a task (so tasks are not mass-marked **blocked** for that reason).  
- Other failures during AI execution can still mark a task **blocked**; see PRD and run **`error_message`** in SQLite.

---

## 7. Command 6 — Install cron jobs

```bash
bash ~/agents/agent-services/install.sh
```

### What it does

- Appends a **crontab** block (once) for:
  - **`workers/task_worker.py`** — **every 2 hours** (imports from `tasks.json` into SQLite; **does not** run `--mode ai` on the execution worker).  
  - **`workers/decision_reviewer.py`** — **daily at 8:00** (separate maintenance job).  
  - **Gmail triage** line is present but **commented out** until you configure credentials.

### What cron does *not* do

- It does **not** automatically run **`system/services/task_worker.py`** on a schedule in the default `install.sh`. So **manual execution** is still something **you** trigger (or you add your own cron line if you explicitly want that).

### Inspect or remove

```bash
crontab -l          # list
crontab -e          # edit — remove the “agent-services managed crons” block to uninstall
```

### Environment variables for cron

- Cron jobs often run with a **minimal environment**. If you later add jobs that need secrets, use **`set -a; source /path/to/.env; set +a`** in the cron line (see `install_crons.sh` in the repo for an example pattern).

---

## 8. Command 7 — Orchestrator (multi-agent plans)

```bash
cd ~/.claude && python3 -m orchestrator \
  --runs-dir /path/to/project/runs/ephemeral \
  --plan swarm_research \
  --goal "Your goal text here" \
  --mode simulate
```

### What it is

- A **separate** subsystem from the SQLite dashboard. It runs **plans** defined under **`~/.claude/agents/plans/`** (e.g. `swarm_research.json`), writes outputs under **`--runs-dir`**, and supports multiple **modes**.

### Replace placeholders

- **`/path/to/project/runs/ephemeral`** — must be the **real** `runs/ephemeral` directory of your **active project** (the same project you passed to `init.sh`). Example: `~/Projects/my-app/runs/ephemeral`.  
- **`--goal`** — natural language description of what the plan should achieve.

### Modes (important)

| Mode | Meaning |
|------|--------|
| **`simulate`** | **Default, safest for learning.** Exercises the plan **without** requiring **`ANTHROPIC_API_KEY`** (no live API execution in the sense of `execute` mode). |
| **`handoff`** | Produces **handoff artifacts**; you complete JSON steps and resume with **`--resume`**, **`--advance`**, **`--finish`** (see CLI help). |
| **`execute`** | **Uses the Anthropic API** — requires **`ANTHROPIC_API_KEY`** and relevant dependencies. |

### Other useful flags

```bash
python3 -m orchestrator --help
```

Examples: **`--reuse-outputs`**, **`--run-id`**, **`--resume`** workflows.

### Relationship to SQLite tasks

- The orchestrator is **not** the same as **`system/services/task_worker.py`**. You can use **both** in one overall workflow, but they **do not automatically replace** each other.

---

## 9. End-to-end flows (cheat sheet)

### A. “I planned tasks in chat and they’re in `~/.claude/tasks.json`”

1. `bash ~/agents/agent-system-base/init.sh <your-project-dir>` (when you need a fresh sync).  
2. `cd ~/agents/agent-services && python3 workers/task_worker.py`  
3. `cd ~/agents/agent-services && python3 system/dashboard/server.py` — open browser, confirm tasks.  
4. `cd ~/agents/agent-services && python3 system/services/task_worker.py --mode manual`  
5. Complete work in your editor; submit via **`POST /api/tasks/{id}/complete`** (dashboard).

### B. “I only want to explore multi-agent plans”

1. Ensure `init.sh` has been run so **`~/.claude/orchestrator`** exists.  
2. `cd ~/.claude && python3 -m orchestrator --runs-dir ... --plan swarm_research --goal "..." --mode simulate`

### C. “Cron should keep importing my JSON tasks”

1. `bash ~/agents/agent-services/install.sh`  
2. Confirm `crontab -l` shows the **agent-services** block.

---

## 10. Troubleshooting (quick)

| Symptom | Likely cause | What to check |
|---------|----------------|----------------|
| Dashboard won’t start | Missing **uvicorn/fastapi** | `pip install -r ~/agents/agent-services/system/dashboard/requirements.txt` |
| Tasks stuck **blocked** in SQLite | Past **AI** runs without API key or other execution errors | Run **`SELECT`/`error_message`** on `runs`; reset tasks to **`pending`** only after fixing the cause (see PRD / operator notes). |
| Everything lands under **Global Claude** | Tasks only in **`~/.claude/tasks.json`** with no **`sqlite_project_slug`** | Use **per-project `tasks.json`** or set **`sqlite_project_slug`** on each row. |
| `init.sh` errors | Bad path or permissions | Pass an **existing** project directory; check `rsync` and disk space. |
| Orchestrator can’t find plan | Wrong **`--plan`** id | File must exist: `~/.claude/agents/plans/<id>.json` |

---

## 11. Where to read next

- **`PRD.md`** — AS-BUILT data model, APIs, and workflows (authoritative for behavior).  
- **`~/.claude/CLAUDE.md`** — How assistants should write **`tasks.json`** and session rules.  
- **`workers/task_worker.py`** module docstring — Import worker flags and optional **`tasks.json`** fields.

---

---

## 12. Operator v1.0 — prompt additions (knowledge + verify + session)

Use these together with your Operator agent definition (e.g. in Claude Code / Cursor).

### 12.1 Knowledge files (add to the Operator’s read list)

- [`docs/requirement_contract.md`](docs/requirement_contract.md) — TRIGGER / INPUT / OUTPUT / CONSTRAINTS / FAILURE PATH.
- [`docs/system_contract.md`](docs/system_contract.md) — stack invariants (SQLite, services, workers, `.claude/` layout).

### 12.2 Verify step (append to the existing checklist)

After your normal verification, confirm explicitly:

- Satisfies **requirement contract**? (TRIGGER handled, INPUT validated, OUTPUT matches spec, CONSTRAINTS met, FAILURE PATH implemented.)

### 12.3 Session log (STEP 8 — file write)

At end of session, **append** an entry to **`[project-root]/.claude/session.md`** using the format in [`docs/session_log_template.md`](docs/session_log_template.md).

---

*This guide aligns with PRD §15 operational commands. If the PRD and this file disagree, **trust the PRD and the code** and update this guide.*
