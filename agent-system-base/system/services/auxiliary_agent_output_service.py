from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import db


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def list_by_project(project_id: int) -> list[dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM auxiliary_agent_outputs
            WHERE project_id = ?
            ORDER BY created_at DESC
            """,
            (project_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def create(
    project_id: int,
    agent_role: str,
    content: str,
    *,
    target_core_agent: str | None = None,
    related_requirement_ref: str | None = None,
    related_decision_id: int | None = None,
) -> dict[str, Any]:
    now = _iso_now()
    with db.connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO auxiliary_agent_outputs (
              project_id, agent_role, content, status,
              target_core_agent, related_requirement_ref, related_decision_id, created_at
            ) VALUES (?, ?, ?, 'pending', ?, ?, ?, ?) RETURNING id
            """,
            (project_id, agent_role, content, target_core_agent, related_requirement_ref, related_decision_id, now),
        )
        oid = cur.lastrowid
        conn.commit()
        row = conn.execute(
            "SELECT * FROM auxiliary_agent_outputs WHERE id = ?", (oid,)
        ).fetchone()
    assert row is not None
    return dict(row)
