"""Proposed action CRUD service."""
from __future__ import annotations

from typing import Optional

import db


def list_pending(project_id: Optional[int] = None) -> list[dict]:
    if project_id is not None:
        with db.get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM proposed_actions WHERE status = 'pending' AND project_id = ? ORDER BY id",
                (project_id,),
            )
            return db.fetchall(cur)
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM proposed_actions WHERE status = 'pending' ORDER BY id"
        )
        return db.fetchall(cur)


def list_all(project_id: Optional[int] = None) -> list[dict]:
    if project_id is not None:
        with db.get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM proposed_actions WHERE project_id = ? ORDER BY id",
                (project_id,),
            )
            return db.fetchall(cur)
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM proposed_actions ORDER BY id")
        return db.fetchall(cur)


def approve(action_id: int) -> dict:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM proposed_actions WHERE id = ?", (action_id,))
        row = db.fetchone(cur)
        if row is None:
            raise LookupError(f"Proposed action {action_id} not found")
        if row["status"] != "pending":
            raise ValueError(f"Action {action_id} is already {row['status']!r}")
        cur.execute(
            """UPDATE proposed_actions SET status = 'approved',
               updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now')
               WHERE id = ?""",
            (action_id,),
        )
        cur.execute("SELECT * FROM proposed_actions WHERE id = ?", (action_id,))
        return db.fetchone(cur)


def reject(action_id: int, note: Optional[str] = None) -> dict:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM proposed_actions WHERE id = ?", (action_id,))
        row = db.fetchone(cur)
        if row is None:
            raise LookupError(f"Proposed action {action_id} not found")
        if row["status"] != "pending":
            raise ValueError(f"Action {action_id} is already {row['status']!r}")
        cur.execute(
            """UPDATE proposed_actions SET status = 'rejected', note = ?,
               updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now')
               WHERE id = ?""",
            (note, action_id),
        )
        cur.execute("SELECT * FROM proposed_actions WHERE id = ?", (action_id,))
        return db.fetchone(cur)
