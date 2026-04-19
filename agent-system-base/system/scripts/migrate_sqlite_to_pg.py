#!/usr/bin/env python3
"""
One-shot migration: local SQLite → Railway Postgres.

Usage:
    DATABASE_URL=postgresql://... python migrate_sqlite_to_pg.py

Re-runnable: uses ON CONFLICT DO NOTHING so existing rows are skipped.
Run from the agent-system-base root or set SQLITE_PATH env var.
"""

import os
import sqlite3
import sys
from pathlib import Path

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    sys.exit("psycopg2-binary is required: pip install psycopg2-binary")

SQLITE_PATH = os.environ.get(
    "SQLITE_PATH",
    str(Path.home() / "agents" / "agent-system-base" / "system" / "db" / "database.sqlite"),
)

PG_URL = os.environ.get("DATABASE_URL", "")
if not PG_URL:
    sys.exit("DATABASE_URL is not set. Export it before running.")

# FK-safe insertion order
TABLES_IN_ORDER = [
    "schema_version",
    "projects",
    "decisions",
    "tasks",
    "runs",
    "memory",
    "blueprints",
    "session_logs",
    "proposed_actions",
    "auxiliary_agent_outputs",
]

# Tables with BIGSERIAL primary keys that need sequence resets after seeding
SEQUENCES = {
    "projects": "projects_id_seq",
    "tasks": "tasks_id_seq",
    "runs": "runs_id_seq",
    "decisions": "decisions_id_seq",
    "memory": "memory_id_seq",
    "blueprints": "blueprints_id_seq",
    "session_logs": "session_logs_id_seq",
    "proposed_actions": "proposed_actions_id_seq",
    "auxiliary_agent_outputs": "auxiliary_agent_outputs_id_seq",
}


def migrate():
    print(f"Source: {SQLITE_PATH}")
    print(f"Target: {PG_URL[:40]}...")

    sq = sqlite3.connect(SQLITE_PATH)
    sq.row_factory = sqlite3.Row
    pg = psycopg2.connect(PG_URL, cursor_factory=psycopg2.extras.RealDictCursor)

    for table in TABLES_IN_ORDER:
        rows = sq.execute(f"SELECT * FROM {table}").fetchall()
        if not rows:
            print(f"  {table}: 0 rows — skip")
            continue

        cols = list(rows[0].keys())
        col_list = ", ".join(f'"{c}"' for c in cols)
        placeholders = ", ".join(["%s"] * len(cols))
        sql = f'INSERT INTO {table} ({col_list}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'

        data = [tuple(r[c] for c in cols) for r in rows]
        with pg.cursor() as cur:
            cur.executemany(sql, data)
        pg.commit()
        print(f"  {table}: {len(rows)} rows inserted (duplicates skipped)")

    # Reset sequences so new inserts get IDs > seeded max
    with pg.cursor() as cur:
        for table, seq in SEQUENCES.items():
            cur.execute(
                f"SELECT setval('{seq}', COALESCE((SELECT MAX(id) FROM {table}), 1))"
            )
    pg.commit()
    print("Sequences reset.")

    sq.close()
    pg.close()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
