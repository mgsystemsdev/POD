# stack_guide.md
# The Operator — System Reference

Read this at every session start before asking Miguel anything.
This is the map of Miguel's system. You must know it completely before touching a single task.

---

## THE THREE LAYERS

Miguel's stack has three distinct layers. Never confuse them. They have different purposes, different directories, and different rules.

### Layer 1 — agent-system-base
Path: ~/agents/agent-system-base

This is the blueprint repo. This is the only layer committed to Git. All code that matters lives here. All Git commands run from here. When Miguel edits code, he edits it here. When you give a Git command, you always say "run this from agent-system-base."

### Layer 2 — agent-services
Path: ~/agents/agent-services

This is the runtime mirror. It is synced from Layer 1 via init.sh. Workers and the dashboard run from here. It is never committed to Git directly. When you give a worker command or dashboard command, you always say "run this from agent-services." If Layer 2 is missing or stale, nothing runs correctly — run init.sh first.

### Layer 3 — ~/.claude
Path: ~/.claude

This is the global Claude layer. Orchestrator, agent definitions, plans, schemas, and tasks.json live here. Also synced by init.sh. This is where the import worker reads tasks from.

### The sync command
When Layer 2 or Layer 3 is stale or missing:
bash ~/agents/agent-system-base/init.sh /path/to/active-project

---

## THE TWO WORKERS

These are completely different. Confusing them is one of the most common failure points.

### Import Worker
Script: workers/task_worker.py
Run from: agent-services
What it does: reads tasks.json from ~/.claude and per-project task files, imports them into SQLite as pending tasks. It does NOT execute anything. It is a data pipeline — work enters the system here.

Command: cd ~/agents/agent-services && python3 workers/task_worker.py
Dry run: cd ~/agents/agent-services && python3 workers/task_worker.py --dry-run

Use when: tasks exist in tasks.json but are not showing up in the dashboard.

### Execution Worker
Script: system/services/task_worker.py
Run from: agent-services
What it does: claims exactly ONE pending task from SQLite, creates a run, builds a prompt, writes it to pending_input, prints READY task_id=... run_id=..., then exits. It does NOT execute the task — it prepares it. Miguel executes it externally in Claude or Cursor.

Command (manual mode): cd ~/agents/agent-services && python3 system/services/task_worker.py --mode manual
Command (specific project): add --project-id [id]

Use when: you are ready to execute the next task from the dashboard.

If the worker exits quietly with no output: there are no pending tasks in SQLite. Run the import worker first or check the dashboard for task status.

---

## THE DASHBOARD

URL: http://127.0.0.1:8765
Start command: cd ~/agents/agent-services && python3 system/dashboard/server.py
Stop: Ctrl+C in the terminal where it is running.

The dashboard shows projects, tasks, and runs. It is the operator's view into SQLite. Miguel uses it to see what is pending, what is in progress, and to submit task completions.

If dashboard won't start: cd ~/agents/agent-services && python3 -m pip install -r system/dashboard/requirements.txt

---

## SQLITE — THE SOURCE OF TRUTH

Path: system/db/database.sqlite (inside agent-system-base, used by agent-services via db.py)
There is ONE database. agent-services does not have its own separate database — it points to the same file.

Key task statuses: pending, in_progress, blocked, done, cancelled, failed
Key run statuses: pending, pending_input, running, success, failed, cancelled

pending_input means: the system prepared a prompt and is waiting for Miguel to execute it and submit the result.

---

## MANUAL EXECUTION LOOP

This is the core cycle for every task:

1. Task exists in SQLite with status pending
2. Run execution worker → task becomes in_progress, run created with pending_input + prompt
3. Miguel copies the prompt from the dashboard
4. Miguel executes the prompt in Claude or Cursor
5. Miguel submits the result: POST /api/tasks/{task_id}/complete with plain text body
6. Task becomes done, run becomes success

Never skip the completion step. A task stuck in in_progress with a run in pending_input means step 5 was never done.

---

## FAILURE DIAGNOSIS

When something breaks, diagnose before fixing. These are the most common failure points and why they happen.

| Symptom | Cause | Fix |
|---------|-------|-----|
| Execution worker exits quietly | No pending tasks in SQLite | Run import worker first |
| Worker import errors | Wrong working directory or PYTHONPATH | Run from agent-services, not agent-system-base |
| Dashboard won't start | Missing uvicorn/fastapi | pip install -r system/dashboard/requirements.txt |
| Port 8765 already in use | Previous dashboard still running | Find and kill the process, then restart |
| Task stuck in in_progress | Completion step never submitted | POST /api/tasks/{id}/complete with output |
| Run stuck in pending_input | Same as above | Same fix |
| Tasks land in Global Claude project | tasks.json has no sqlite_project_slug | Add sqlite_project_slug to each task or use per-project tasks.json |
| init.sh errors | Bad path or permissions | Pass an existing project directory |
| PRD and codebase disagree | Implementation drifted from design | Update PRD before executing more tasks |

Always explain to Miguel in one plain English sentence why the failure happened after fixing it.

---

## PRD ALIGNMENT

The PRD is the contract. The codebase must match it. When they disagree, every prompt generated from the PRD will be slightly wrong and produce code that does not fit.

Check PRD alignment at the start of every scope — not every task, every scope.

Ask Miguel: "Has anything changed in the implementation since the PRD was written that the PRD does not reflect?"

If yes: update the PRD first. Do not execute tasks against a PRD that does not reflect reality.

Signs of drift:
- Implementation uses a different architecture than the PRD describes
- A constraint in the PRD is no longer enforced in the code
- A component described in the PRD does not exist or has been renamed
- The API contracts in the PRD do not match what the code actually exposes

If drift is significant: redirect to The Architect (GPT 1) to update the PRD formally before proceeding.

---

## DIRECTORY RULES (never get this wrong)

| Action | Directory |
|--------|-----------|
| Git commands | agent-system-base |
| Run workers | agent-services |
| Run dashboard | agent-services |
| Run orchestrator | ~/.claude |
| Edit code | agent-system-base |
| Commit code | agent-system-base |

If Miguel runs a Git command from agent-services: stop and correct immediately.

---

## SESSION LOG FORMAT

The Operator appends this entry to [project-root]/.claude/session.md at the end of every session. Never overwrite — always append.

```
## [YYYY-MM-DD HH:MM] — Session [N]

Scope: [scope name] — Tier [1/2/3]
Completed: [TASK-IDs done this session]
In progress: [TASK-ID if stopped mid-task, otherwise none]
Next task: [TASK-ID]: [title]
Git: clean on main
Open issues: [blockers, risks, anything next session must know]
Context: [2 sentences — what was built this session, what the next task needs from it]
```

Commit after writing: git add .claude/session.md && git commit -m "ops: session log [date]"
