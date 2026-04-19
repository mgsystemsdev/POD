"""Run CRUD service."""
from __future__ import annotations

from typing import Optional

import db


def get_runs_for_task(task_id: int) -> list[dict]:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM runs WHERE task_id = ? ORDER BY id",
            (task_id,),
        )
        return db.fetchall(cur)


def list_recent_runs(
    project_id: Optional[int] = None,
    limit: int = 500,
) -> list[dict]:
    if project_id is not None:
        with db.get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT r.* FROM runs r
                   JOIN tasks t ON t.id = r.task_id
                   WHERE t.project_id = ?
                   ORDER BY r.id DESC LIMIT ?""",
                (project_id, limit),
            )
            return db.fetchall(cur)
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,))
        return db.fetchall(cur)


def create_run(task_id: int, mode: str = "auto") -> dict:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO runs (task_id, mode, status) VALUES (?, ?, 'pending')",
            (task_id, mode),
        )
        row_id = cur.lastrowid
        cur.execute("SELECT * FROM runs WHERE id = ?", (row_id,))
        return db.fetchone(cur)


def update_run(
    run_id: int,
    status: str,
    output: Optional[str] = None,
) -> dict | None:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """UPDATE runs SET status = ?, output = ?,
               updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now')
               WHERE id = ?""",
            (status, output, run_id),
        )
        cur.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        return db.fetchone(cur)


def complete_manual_run(run_id: int, output: str) -> tuple[dict, dict]:
    """Mark a pending_input run as success and return (updated_task, updated_run)."""
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        run = db.fetchone(cur)
        if run is None:
            raise ValueError(f"Run {run_id} not found")
        if run["status"] != "pending_input":
            raise ValueError(f"Run {run_id} is not in pending_input state")
        cur.execute(
            """UPDATE runs SET status = 'success', output = ?,
               updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now')
               WHERE id = ?""",
            (output, run_id),
        )
        cur.execute(
            """UPDATE tasks SET status = 'done',
               updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now')
               WHERE id = ?""",
            (run["task_id"],),
        )
        cur.execute("SELECT * FROM tasks WHERE id = ?", (run["task_id"],))
        updated_task = db.fetchone(cur)
        cur.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        updated_run = db.fetchone(cur)
        return updated_task, updated_run
