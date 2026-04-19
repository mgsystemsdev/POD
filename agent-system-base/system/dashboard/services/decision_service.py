"""Decision CRUD service."""
from __future__ import annotations

from typing import Optional

import db


def list_decisions(project_id: Optional[int] = None) -> list[dict]:
    if project_id is not None:
        with db.get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM decisions WHERE project_id = ? ORDER BY id",
                (project_id,),
            )
            return db.fetchall(cur)
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM decisions ORDER BY id")
        return db.fetchall(cur)


def get_decision(decision_id: int) -> dict | None:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,))
        return db.fetchone(cur)


def add_decision(
    title: str,
    content: str,
    project_id: Optional[int] = None,
) -> dict:
    if not title:
        raise ValueError("title is required")
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO decisions (project_id, title, content) VALUES (?, ?, ?)",
            (project_id, title, content),
        )
        row_id = cur.lastrowid
        cur.execute("SELECT * FROM decisions WHERE id = ?", (row_id,))
        return db.fetchone(cur)
