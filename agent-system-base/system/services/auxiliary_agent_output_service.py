from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import db
import project_service


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
    specialist_table: str | None = None,
    specialist_id: int | None = None,
) -> dict[str, Any]:
    now = _iso_now()
    with db.connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO auxiliary_agent_outputs (
              project_id, agent_role, content, status,
              target_core_agent, related_requirement_ref, related_decision_id,
              specialist_table, specialist_id, created_at
            ) VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?) RETURNING id
            """,
            (
                project_id, agent_role, content, target_core_agent, related_requirement_ref, related_decision_id,
                specialist_table, specialist_id, now
            ),
        )
        oid = cur.lastrowid
        conn.commit()
        row = conn.execute(
            "SELECT * FROM auxiliary_agent_outputs WHERE id = ?", (oid,)
        ).fetchone()
    assert row is not None
    return dict(row)


def upsert_cli_mirror_output(
    project_id: int,
    agent_role: str,
    content: str,
    *,
    dry_run: bool,
) -> tuple[str, str]:
    """
    Replace unmanaged auxiliary rows for this role with a single CLI-authored row.

    Deletes only rows where ``specialist_table`` is null/empty (never touches
    security_findings / db_recommendations / adversarial_critiques links).
    """
    if not project_service.project_exists(project_id):
        return "error", f"unknown project_id: {project_id}"
    body = (content or "").strip()
    if not body:
        return "skipped", f"{agent_role}: empty file"

    if dry_run:
        return "dry-run", f"would replace CLI mirror for role={agent_role!r} ({len(body)} chars)"

    now = _iso_now()
    role = (agent_role or "").strip()
    if not role:
        return "error", "agent_role is required"

    with db.connect() as conn:
        conn.execute(
            """
            DELETE FROM auxiliary_agent_outputs
            WHERE project_id = ? AND agent_role = ?
              AND (specialist_table IS NULL OR specialist_table = '')
            """,
            (project_id, role),
        )
        conn.execute(
            """
            INSERT INTO auxiliary_agent_outputs (
              project_id, agent_role, content, status,
              target_core_agent, related_requirement_ref, related_decision_id,
              specialist_table, specialist_id, created_at
            ) VALUES (?, ?, ?, 'approved', NULL, NULL, NULL, NULL, NULL, ?)
            """,
            (project_id, role, body, now),
        )
        conn.commit()
    return "updated", f"auxiliary CLI mirror role={role!r}"


def create_security_finding(
    project_id: int,
    agent_role: str,
    content: str,
    severity: str,
    vulnerability_desc: str,
    *,
    cve_id: str | None = None,
    component: str | None = None,
    remediation_steps: str | None = None,
) -> dict[str, Any]:
    now = _iso_now()
    with db.connect() as conn:
        # 1. Create the base auxiliary output
        base = create(project_id, agent_role, content)
        aux_id = base["id"]

        # 2. Create the specialized finding
        cur = conn.execute(
            """
            INSERT INTO security_findings (
                project_id, aux_output_id, cve_id, severity, component, vulnerability_desc, remediation_steps, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id
            """,
            (project_id, aux_id, cve_id, severity, component, vulnerability_desc, remediation_steps, now),
        )
        sid = cur.lastrowid

        # 3. Link back to the base
        conn.execute(
            "UPDATE auxiliary_agent_outputs SET specialist_table = 'security_findings', specialist_id = ? WHERE id = ?",
            (sid, aux_id),
        )
        conn.commit()
        
        row = conn.execute("SELECT * FROM security_findings WHERE id = ?", (sid,)).fetchone()
        assert row is not None
        return dict(row)


def create_db_recommendation(
    project_id: int,
    agent_role: str,
    content: str,
    recommendation_type: str,
    rec_content: str,
    *,
    table_name: str | None = None,
    performance_impact: str | None = None,
) -> dict[str, Any]:
    now = _iso_now()
    with db.connect() as conn:
        base = create(project_id, agent_role, content)
        aux_id = base["id"]

        cur = conn.execute(
            """
            INSERT INTO db_recommendations (
                project_id, aux_output_id, table_name, recommendation_type, content, performance_impact, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id
            """,
            (project_id, aux_id, table_name, recommendation_type, rec_content, performance_impact, now),
        )
        rid = cur.lastrowid

        conn.execute(
            "UPDATE auxiliary_agent_outputs SET specialist_table = 'db_recommendations', specialist_id = ? WHERE id = ?",
            (rid, aux_id),
        )
        conn.commit()
        
        row = conn.execute("SELECT * FROM db_recommendations WHERE id = ?", (rid,)).fetchone()
        assert row is not None
        return dict(row)
