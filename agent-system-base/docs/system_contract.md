# System contract (Operator knowledge)

Stack invariants for the personal execution system:

- **SQLite** is the default system of record for tasks, runs, proposals, and (when migrated) project-scoped blueprints, session logs, decisions, and memory. The default file path is set in `system/services/db.py` (`DATABASE_PATH`).
- **Optional Postgres:** when the environment variable **`DATABASE_URL`** is set to a URL starting with `postgres://` or `postgresql://`, `db.py` uses the Postgres adapter and migrations under `system/db/migrations_pg/` instead of the SQLite file (see `system/services/db.py` for behavior).
- **Service layer only** for DB writes; HTTP routes call services.
- **Import worker** bridges `tasks.json` → SQLite; **execution worker** claims one task per run.
- **Per-project roots** use `.claude/` for `project.md`, `tasks.json`, `session.md`, `decisions.md`; root `CLAUDE.md` / `AGENTS.md` stay at repo root.

When in doubt, follow **PRD.md** AS-BUILT over TARGET.
