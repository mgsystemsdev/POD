"""Auxiliary agent output CRUD service."""
from __future__ import annotations

from typing import Optional

import db


def list_by_project(project_id: int) -> list[dict]:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM auxiliary_agent_outputs WHERE project_id = ? ORDER BY id DESC",
            (project_id,),
        )
        return db.fetchall(cur)


def create(
    project_id: int,
    agent_role: str,
    content: str,
    target_core_agent: Optional[str] = None,
    related_requirement_ref: Optional[str] = None,
    related_decision_id: Optional[int] = None,
) -> dict:
    if not agent_role:
        raise ValueError("agent_role is required")
    if not content:
        raise ValueError("content is required")
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO auxiliary_agent_outputs
               (project_id, agent_role, content, target_core_agent,
                related_requirement_ref, related_decision_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (project_id, agent_role, content, target_core_agent,
             related_requirement_ref, related_decision_id),
        )
        row_id = cur.lastrowid
        cur.execute(
            "SELECT * FROM auxiliary_agent_outputs WHERE id = ?", (row_id,)
        )
        return db.fetchone(cur)
