from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import db
import project_service


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_approval(row: Any) -> dict[str, Any]:
    d = dict(row)
    return {
        "id": d["id"],
        "project_id": d["project_id"],
        "entity_type": d["entity_type"],
        "entity_id": d["entity_id"],
        "approver_role": d["approver_role"],
        "decision": d["decision"],
        "reason": d["reason"],
        "created_at": d["created_at"],
    }


def record_approval(
    project_id: int,
    entity_type: str,
    entity_id: int,
    decision: str,
    reason: str | None = None,
    approver_role: str = "human_operator",
) -> dict[str, Any]:
    if not project_service.project_exists(project_id):
        raise ValueError(f"unknown project_id: {project_id}")
    if decision not in ("approved", "rejected"):
        raise ValueError(f"invalid decision: {decision}")
    now = _iso_now()
    with db.connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO approvals (project_id, entity_type, entity_id, approver_role, decision, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id
            """,
            (project_id, entity_type, entity_id, approver_role, decision, reason, now),
        )
        aid = cur.lastrowid
        conn.commit()
        row = conn.execute("SELECT * FROM approvals WHERE id = ?", (aid,)).fetchone()
        assert row is not None
        return _row_to_approval(row)


def list_by_entity(entity_type: str, entity_id: int) -> list[dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM approvals WHERE entity_type = ? AND entity_id = ? ORDER BY created_at DESC",
            (entity_type, entity_id),
        ).fetchall()
        return [_row_to_approval(r) for r in rows]


def list_by_project(project_id: int) -> list[dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM approvals WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        ).fetchall()
        return [_row_to_approval(r) for r in rows]
