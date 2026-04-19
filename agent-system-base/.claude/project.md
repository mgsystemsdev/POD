# Agent System Base — Project Blueprint

**Repo:** `~/agents/agent-system-base` — canonical blueprint for the personal AI execution stack. **Runtime mirror:** `~/agents/agent-services` (via `init.sh`). **Global Claude layer:** `~/.claude`.

> Root `PRD.md` is the full product spec (AS-BUILT vs TARGET). Root `tasks.json` is the **as-built execution plan** for the Claude worker feature — **not** the import queue. Per-project queue for this repo lives in **this file’s sibling** `.claude/tasks.json` (empty until used).

---

## Overview

Local, human-in-the-loop stack: **SQLite** for projects, tasks, runs, proposals; **FastAPI** dashboard; **import worker** (`tasks.json` → SQLite); **execution worker** (claim one task, manual or AI); optional orchestrator under `~/.claude`.

---

## Problem

Separate **intent** (tasks), **execution history** (runs), and **governed mutations** (proposed actions → approve) with an auditable trail and per-project context.

---

## Stack

- Python 3, SQLite (raw SQL), FastAPI, uvicorn
- Services: `system/services/` — **all** DB access through services
- Dashboard: `system/dashboard/server.py` + `index.html`
- Migrations: `system/db/migrations/*.sql`

---

## Architecture

| Piece | Path |
|-------|------|
| DB | `system/db/database.sqlite` (`db.py` → `DATABASE_PATH`) |
| Migrations | Applied on `db.connect()` |
| Import worker | `workers/task_worker.py` → synced to agent-services |
| Execution worker | `system/services/task_worker.py` |

---

## Critical constraints

- AS-BUILT in `PRD.md` wins over TARGET until shipped.
- No direct SQL from HTTP routes — use services.
- Raw SQL only — no ORM.

---

## Current state

Migrations m001–m007 applied; dashboard + workers operational; project-scoped blueprints/session logs/decisions/memory are **TARGET** items being implemented in this build wave.

---

## Next scope

See root `PRD.md` §14 and active tasks. Standard `.claude/` layout lives alongside skills under `.claude/skills/`.
