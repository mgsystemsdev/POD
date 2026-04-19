"""Memory (key-value store per project) service."""
from __future__ import annotations

from typing import Optional

import db


def list_memory(project_id: Optional[int] = None) -> list[dict]:
    if project_id is not None:
        with db.get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM memory WHERE project_id = ? ORDER BY key",
                (project_id,),
            )
            return db.fetchall(cur)
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM memory ORDER BY project_id, key")
        return db.fetchall(cur)


def upsert_memory(project_id: int, key: str, value: str) -> dict:
    if not key:
        raise ValueError("key is required")
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO memory (project_id, key, value)
               VALUES (?, ?, ?)
               ON CONFLICT(project_id, key) DO UPDATE SET
                 value = excluded.value,
                 updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now')""",
            (project_id, key, value),
        )
        cur.execute(
            "SELECT * FROM memory WHERE project_id = ? AND key = ?",
            (project_id, key),
        )
        return db.fetchone(cur)
