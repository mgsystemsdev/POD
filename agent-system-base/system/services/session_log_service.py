from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import db
import project_service

# Upsert target for ``push_claude_artifacts`` / session markdown file
FILE_MIRROR_SESSION_SOURCE_KEY = "claude_session_md"
FILE_MIRROR_SESSION_DATE_LABEL = ".claude/session.md (synced)"


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_session_log(row: Any) -> dict[str, Any]:
    d = dict(row)
    return {
        "id": d["id"],
        "project_id": d["project_id"],
        "agent": d.get("agent"),
        "scope_active": d.get("scope_active"),
        "tasks_completed": d.get("tasks_completed"),
        "next_task": d.get("next_task"),
        "git_state": d.get("git_state"),
        "open_issues": d.get("open_issues"),
        "notes": d.get("notes"),
        "session_date": d["session_date"],
        "created_at": d["created_at"],
        "source_key": d.get("source_key"),
    }


def create(
    project_id: int,
    session_date: str,
    *,
    agent: str | None = None,
    scope_active: str | None = None,
    tasks_completed: str | None = None,
    next_task: str | None = None,
    git_state: str | None = None,
    open_issues: str | None = None,
    notes: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    if not project_service.project_exists(project_id):
        raise ValueError(f"unknown project_id: {project_id}")
    sd = (session_date or "").strip()
    if not sd:
        raise ValueError("session_date is required")
    now = created_at or _iso_now()
    with db.connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO session_logs (
              project_id, agent, scope_active, tasks_completed, next_task,
              git_state, open_issues, notes, session_date, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id
            """,
            (
                project_id,
                agent,
                scope_active,
                tasks_completed,
                next_task,
                git_state,
                open_issues,
                notes,
                sd,
                now,
            ),
        )
        sid = cur.lastrowid
        conn.commit()
        row = conn.execute("SELECT * FROM session_logs WHERE id = ?", (sid,)).fetchone()
        assert row is not None
        return _row_to_session_log(row)


def get_latest(project_id: int) -> dict[str, Any] | None:
    with db.connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM session_logs
            WHERE project_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (project_id,),
        ).fetchone()
        return _row_to_session_log(row) if row else None


def list_by_project(project_id: int, *, limit: int = 100) -> list[dict[str, Any]]:
    lim = max(1, min(int(limit), 500))
    with db.connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM session_logs
            WHERE project_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (project_id, lim),
        ).fetchall()
        return [_row_to_session_log(r) for r in rows]


def get_file_mirror_session(project_id: int) -> dict[str, Any] | None:
    """Return the synced session markdown row if present."""
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM session_logs WHERE project_id = ? AND source_key = ?",
            (project_id, FILE_MIRROR_SESSION_SOURCE_KEY),
        ).fetchone()
        return _row_to_session_log(row) if row else None


def upsert_file_mirror_session(project_id: int, content: str) -> dict[str, Any]:
    """
    Idempotent row for ``.claude/session.md`` (or ``sessions.md``) — **Session Log** tab.

    Full file body in ``notes``; ``session_date`` is a fixed label for the UI heading.
    """
    if not project_service.project_exists(project_id):
        raise ValueError(f"unknown project_id: {project_id}")
    notes = content.strip() if isinstance(content, str) else ""
    if not notes:
        raise ValueError("content is required")
    now = _iso_now()
    sd = FILE_MIRROR_SESSION_DATE_LABEL
    sk = FILE_MIRROR_SESSION_SOURCE_KEY
    with db.connect() as conn:
        row = conn.execute(
            "SELECT id FROM session_logs WHERE project_id = ? AND source_key = ?",
            (project_id, sk),
        ).fetchone()
        if row:
            sid = int(row["id"])
            conn.execute(
                """
                UPDATE session_logs
                SET notes = ?, session_date = ?, created_at = ?
                WHERE id = ?
                """,
                (notes, sd, now, sid),
            )
            conn.commit()
            out = conn.execute("SELECT * FROM session_logs WHERE id = ?", (sid,)).fetchone()
            assert out is not None
            return _row_to_session_log(out)
        cur = conn.execute(
            """
            INSERT INTO session_logs (
              project_id, agent, scope_active, tasks_completed, next_task,
              git_state, open_issues, notes, session_date, created_at, source_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id
            """,
            (
                project_id,
                None,
                None,
                None,
                None,
                None,
                None,
                notes,
                sd,
                now,
                sk,
            ),
        )
        sid = cur.lastrowid
        conn.commit()
        out = conn.execute("SELECT * FROM session_logs WHERE id = ?", (sid,)).fetchone()
        assert out is not None
        return _row_to_session_log(out)
