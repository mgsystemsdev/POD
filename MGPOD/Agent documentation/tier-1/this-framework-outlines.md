# This framework outlines

## Layer 1 — Thinking layer

### System purpose

External cognitive engine for ideation, design, and high-level decisions **before** code is written.

### Components

Four specialized ChatGPT agents as the **team**:

| Role | Responsibility |
| :--- | :--- |
| **Architect** | Translates ideas into project definitions and PRDs. |
| **Spec Gate** | Decomposes designs into atomic, executable tasks in `tasks.json`. |
| **Strategist** | On-call advisor for mid-execution architecture and risk. |
| **Operator** | Session continuity and terminal discipline. |

### Handoff protocol (V1)

Agents produce structured Markdown and JSON; the user manually copies outputs into the project repository.

---

## Layer 2 — Knowledge layer

### System purpose

**Project brain** and single source of project-specific context on disk.

### Location

`.claude/context/` inside each project repository.

### Schema and key entities

| File | Role |
| :--- | :--- |
| `project.md` | Definitive PRD and architectural contract. |
| `tasks.json` | Machine-ready work queue for ingestion. |
| `session.md` | Session continuity (where to resume). |
| `decisions.md` | Architectural choices and rationale. |
| `MEMORY.md` | Patterns and gotchas for tool grounding. |

---

## Layer 3 — Sync layer

### System purpose

Unidirectional bridge from **authored knowledge** (files) to **operational state** (database) to reduce drift.

### Primary tool

`agents push` CLI.

### Workflow

- **sync_worker:** reads `.claude/context/*.md` → SQLite mirror.
- **import_worker:** reads `tasks.json` → SQLite `tasks` table.

### Constraint

Data flows **disk → database** only; the database does not overwrite authored context files.

---

## Layer 4 — Data layer

### System purpose

Persistent operational record and cross-project visibility for the control plane.

### Components

Single-file **SQLite** database.

### Primary entities

- **projects:** managed repositories.
- **tasks** and **runs:** queue and execution history.
- **blueprints**, **decisions**, **session_logs:** mirrors of Layer 2 artifacts.
- **proposed_actions:** human gate for internal agent writes.

---

## Layer 5 — Dashboard and workers

### System purpose

Control plane for human-governed transitions and background processing.

### Dashboard UI (`localhost:8765`)

10-tab interface for tasks, blueprints, decisions, and related views.

### Key interface

**Actions** tab: mandatory gate to approve or reject agent proposals before they become real.

### Workers

| Worker | Role |
| :--- | :--- |
| `task_worker.py` | Claims pending tasks from SQLite; prepares execution prompts (requires Anthropic API key). |
| `decision_reviewer.py` | Daily audit; flags decisions for 30-day review. |

---

## Layer 6 — Execution layer

### System purpose

Repo-aware implementation and editing.

### Components

- **Claude Code:** complex builds, multi-file reasoning, step-zero analysis.
- **Cursor:** frontend/UI, single-file edits, unit tests.

### Integration rule

Both tools use thin adapters (`CLAUDE.md`, `.cursor/rules/`) pointing at shared **Layer 2** `.claude/context/` — same grounding, no duplicated stacks.

---

## Layer 7 — Version control

### System purpose

Permanent, authoritative record of what shipped; team-style discipline for a solo developer.

### Tooling

Git and GitHub.

### Workflow constraints

- **Isolation:** one branch per task (e.g. `feature/TASK-001`).
- **PR rule:** merges via GitHub PR UI, not ad-hoc local merges, for self-review.
- **Stability:** `main` stays protected and shippable.

See also: [Version Control (Layer 7)](version-control-layer-7.md).
