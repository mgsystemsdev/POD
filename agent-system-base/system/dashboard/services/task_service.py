"""Task CRUD service."""
from __future__ import annotations

from typing import Optional

import db


def list_tasks(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
) -> list[dict]:
    clauses: list[str] = []
    params: list = []
    if project_id is not None:
        clauses.append("project_id = ?")
        params.append(project_id)
    if status is not None:
        clauses.append("status = ?")
        params.append(status)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM tasks {where} ORDER BY id", params)
        return db.fetchall(cur)


def get_task(task_id: int) -> dict | None:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return db.fetchone(cur)


def create_task(
    project_id: int,
    title: str,
    description: Optional[str] = None,
    priority: str = "normal",
    notes: Optional[str] = None,
    correlation_id: Optional[str] = None,
    requirement_ref: Optional[str] = None,
    decision_id: Optional[int] = None,
) -> dict:
    if not title:
        raise ValueError("title is required")
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO tasks
               (project_id, title, description, priority, notes,
                correlation_id, requirement_ref, decision_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (project_id, title, description, priority, notes,
             correlation_id, requirement_ref, decision_id),
        )
        row_id = cur.lastrowid
        cur.execute("SELECT * FROM tasks WHERE id = ?", (row_id,))
        return db.fetchone(cur)


def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    notes: Optional[str] = None,
    correlation_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
) -> dict | None:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = db.fetchone(cur)
        if row is None:
            return None
        fields = {
            "title": title if title is not None else row["title"],
            "description": description if description is not None else row["description"],
            "notes": notes if notes is not None else row["notes"],
            "correlation_id": correlation_id if correlation_id is not None else row["correlation_id"],
            "status": status if status is not None else row["status"],
            "priority": priority if priority is not None else row["priority"],
        }
        cur.execute(
            """UPDATE tasks SET
               title = ?, description = ?, notes = ?, correlation_id = ?,
               status = ?, priority = ?,
               updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now')
               WHERE id = ?""",
            (*fields.values(), task_id),
        )
        cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return db.fetchone(cur)


def update_status(task_id: int, status: str) -> dict | None:
    return update_task(task_id, status=status)


def delete_task(task_id: int) -> bool:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cur.rowcount > 0
