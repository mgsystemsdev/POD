"""Session log CRUD service."""
from __future__ import annotations

from typing import Optional

import db


def list_by_project(project_id: int, limit: int = 100) -> list[dict]:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM session_logs WHERE project_id = ? ORDER BY id DESC LIMIT ?",
            (project_id, limit),
        )
        return db.fetchall(cur)


def get_latest(project_id: int) -> dict | None:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM session_logs WHERE project_id = ? ORDER BY id DESC LIMIT 1",
            (project_id,),
        )
        return db.fetchone(cur)


def create(
    project_id: int,
    session_date: str,
    agent: Optional[str] = None,
    scope_active: Optional[str] = None,
    tasks_completed: Optional[str] = None,
    next_task: Optional[str] = None,
    git_state: Optional[str] = None,
    open_issues: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    if not session_date:
        raise ValueError("session_date is required")
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO session_logs
               (project_id, session_date, agent, scope_active, tasks_completed,
                next_task, git_state, open_issues, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (project_id, session_date, agent, scope_active, tasks_completed,
             next_task, git_state, open_issues, notes),
        )
        row_id = cur.lastrowid
        cur.execute("SELECT * FROM session_logs WHERE id = ?", (row_id,))
        return db.fetchone(cur)
