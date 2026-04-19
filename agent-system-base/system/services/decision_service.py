from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import db
import project_service

# Upsert target for ``push_claude_artifacts`` / ``.claude/decisions.md``
FILE_MIRROR_DECISION_TITLE = "Synced — .claude/decisions.md"
FILE_MIRROR_DECISION_SOURCE_KEY = "claude_decisions_md"


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_decision(row: Any) -> dict[str, Any]:
    d = dict(row)
    return {
        "id": d["id"],
        "title": d["title"],
        "content": d["content"],
        "created_at": d["created_at"],
        "project_id": d.get("project_id"),
        "source_key": d.get("source_key"),
        "created_by": d.get("created_by"),
        "correlation_id": d.get("correlation_id"),
        "source_proposal_id": d.get("source_proposal_id"),
    }


def add_decision(
    title: str,
    content: str,
    *,
    project_id: int | None = None,
    created_by: str | None = None,
    correlation_id: str | None = None,
    source_proposal_id: int | None = None,
) -> dict[str, Any]:
    """Append a decision row. No update or delete — append-only."""
    t = title.strip() if isinstance(title, str) else ""
    c = content.strip() if isinstance(content, str) else ""
    if not t:
        raise ValueError("title is required")
    if not c:
        raise ValueError("content is required")
    now = _iso_now()
    with db.connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO decisions (title, content, created_at, project_id, created_by, correlation_id, source_proposal_id)
            VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id
            """,
            (t, c, now, project_id, created_by, correlation_id, source_proposal_id),
        )
        did = cur.lastrowid
        conn.commit()
        row = conn.execute("SELECT * FROM decisions WHERE id = ?", (did,)).fetchone()
        assert row is not None
        return _row_to_decision(row)


def list_decisions(*, project_id: int | None = None) -> list[dict[str, Any]]:
    """Return decisions oldest first (by ``created_at`` ASC, then ``id`` ASC)."""
    with db.connect() as conn:
        if project_id is not None:
            rows = conn.execute(
                """
                SELECT * FROM decisions
                WHERE project_id = ?
                ORDER BY created_at ASC, id ASC
                """,
                (project_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM decisions ORDER BY created_at ASC, id ASC"
            ).fetchall()
        return [_row_to_decision(r) for r in rows]


def get_file_mirror_decision(project_id: int) -> dict[str, Any] | None:
    """Return the synced ``.claude/decisions.md`` row if present."""
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM decisions WHERE project_id = ? AND source_key = ?",
            (project_id, FILE_MIRROR_DECISION_SOURCE_KEY),
        ).fetchone()
        return _row_to_decision(row) if row else None


def upsert_file_mirror_decision(project_id: int, content: str) -> dict[str, Any]:
    """
    Idempotent row for ``.claude/decisions.md`` — shows on dashboard **Decisions** tab.

    One row per (project_id, FILE_MIRROR_DECISION_SOURCE_KEY); content replaced on each push.
    """
    if not project_service.project_exists(project_id):
        raise ValueError(f"unknown project_id: {project_id}")
    c = content.strip() if isinstance(content, str) else ""
    if not c:
        raise ValueError("content is required")
    now = _iso_now()
    title = FILE_MIRROR_DECISION_TITLE
    sk = FILE_MIRROR_DECISION_SOURCE_KEY
    with db.connect() as conn:
        row = conn.execute(
            "SELECT id FROM decisions WHERE project_id = ? AND source_key = ?",
            (project_id, sk),
        ).fetchone()
        if row:
            did = int(row["id"])
            conn.execute(
                "UPDATE decisions SET title = ?, content = ? WHERE id = ?",
                (title, c, did),
            )
            conn.commit()
            out = conn.execute("SELECT * FROM decisions WHERE id = ?", (did,)).fetchone()
            assert out is not None
            return _row_to_decision(out)
        cur = conn.execute(
            """
            INSERT INTO decisions (title, content, created_at, project_id, source_key)
            VALUES (?, ?, ?, ?, ?) RETURNING id
            """,
            (title, c, now, project_id, sk),
        )
        did = cur.lastrowid
        conn.commit()
        out = conn.execute("SELECT * FROM decisions WHERE id = ?", (did,)).fetchone()
        assert out is not None
        return _row_to_decision(out)
