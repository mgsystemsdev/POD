from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import db
import project_service


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_backlog(row: Any) -> dict[str, Any]:
    d = dict(row)
    return {
        "id": d["id"],
        "project_id": d["project_id"],
        "title": d["title"],
        "description": d["description"],
        "submitted_by": d["submitted_by"],
        "status": d["status"],
        "created_at": d["created_at"],
        "updated_at": d["updated_at"],
    }


def create(
    project_id: int,
    title: str,
    description: str | None = None,
    submitted_by: str = "human",
) -> dict[str, Any]:
    if not project_service.project_exists(project_id):
        raise ValueError(f"unknown project_id: {project_id}")
    now = _iso_now()
    with db.connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO backlog (project_id, title, description, submitted_by, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'backlog', ?, ?) RETURNING id
            """,
            (project_id, title, description, submitted_by, now, now),
        )
        bid = cur.lastrowid
        conn.commit()
        row = conn.execute("SELECT * FROM backlog WHERE id = ?", (bid,)).fetchone()
        assert row is not None
        return _row_to_backlog(row)


def list_by_project(project_id: int, status: str | None = None) -> list[dict[str, Any]]:
    with db.connect() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM backlog WHERE project_id = ? AND status = ? ORDER BY created_at DESC",
                (project_id, status),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM backlog WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            ).fetchall()
        return [_row_to_backlog(r) for r in rows]


def update_status(backlog_id: int, status: str) -> dict[str, Any] | None:
    if status not in ("backlog", "promoted", "rejected"):
        raise ValueError(f"invalid status: {status}")
    now = _iso_now()
    with db.connect() as conn:
        conn.execute(
            "UPDATE backlog SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, backlog_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM backlog WHERE id = ?", (backlog_id,)).fetchone()
        return _row_to_backlog(row) if row else None
