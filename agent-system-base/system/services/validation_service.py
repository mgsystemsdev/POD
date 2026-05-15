from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import db
import project_service


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_validation(row: Any) -> dict[str, Any]:
    d = dict(row)
    return {
        "id": d["id"],
        "project_id": d["project_id"],
        "blueprint_id": d["blueprint_id"],
        "status": d["status"],
        "findings": d["findings"],
        "created_at": d["created_at"],
    }


def record_validation(
    project_id: int,
    blueprint_id: int,
    status: str,
    findings: str | None = None,
) -> dict[str, Any]:
    if not project_service.project_exists(project_id):
        raise ValueError(f"unknown project_id: {project_id}")
    if status not in ("passed", "blocked"):
        raise ValueError(f"invalid status: {status}")
    now = _iso_now()
    with db.connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO validations (project_id, blueprint_id, status, findings, created_at)
            VALUES (?, ?, ?, ?, ?) RETURNING id
            """,
            (project_id, blueprint_id, status, findings, now),
        )
        vid = cur.lastrowid
        conn.commit()
        row = conn.execute("SELECT * FROM validations WHERE id = ?", (vid,)).fetchone()
        assert row is not None
        return _row_to_validation(row)


def list_by_blueprint(blueprint_id: int) -> list[dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM validations WHERE blueprint_id = ? ORDER BY created_at DESC",
            (blueprint_id,),
        ).fetchall()
        return [_row_to_validation(r) for r in rows]


def list_by_project(project_id: int) -> list[dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM validations WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        ).fetchall()
        return [_row_to_validation(r) for r in rows]
