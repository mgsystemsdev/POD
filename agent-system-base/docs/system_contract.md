# System contract (Operator knowledge)

Stack invariants for the personal execution system:

- **SQLite** is the system of record for tasks, runs, proposals, and (when migrated) project-scoped blueprints, session logs, decisions, and memory.
- **Service layer only** for DB writes; HTTP routes call services.
- **Import worker** bridges `tasks.json` → SQLite; **execution worker** claims one task per run.
- **Per-project roots** use `.claude/` for `project.md`, `tasks.json`, `session.md`, `decisions.md`; root `CLAUDE.md` / `AGENTS.md` stay at repo root.

When in doubt, follow **PRD.md** AS-BUILT over TARGET.
