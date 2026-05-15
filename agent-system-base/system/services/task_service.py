from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import db
import project_service

_STATUSES = frozenset(
    {"pending", "queued", "in_progress", "blocked", "done", "cancelled", "failed"}
)
_PRIORITIES = frozenset({"low", "normal", "high", "urgent"})
_TYPES = frozenset({"feature", "bug", "chore", "research", "maintenance", "other"})
_SOURCES = frozenset(
    {"manual", "cron", "api", "import", "orchestrator", "other", "project_import"}
)


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_timestamp(iso_str: str) -> str:
    """Normalize an ISO-8601 timestamp to UTC ``...Z`` form (same canonical shape as ``_iso_now()``)."""
    s = iso_str.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc).replace(microsecond=0)
    return dt.isoformat().replace("+00:00", "Z")


def _validate_status(value: str) -> None:
    if value not in _STATUSES:
        raise ValueError(f"invalid status: {value!r}")


def _validate_priority(value: str) -> None:
    if value not in _PRIORITIES:
        raise ValueError(f"invalid priority: {value!r}")


def _validate_type(value: str) -> None:
    if value not in _TYPES:
        raise ValueError(f"invalid type: {value!r}")


def _validate_source(value: str) -> None:
    if value not in _SOURCES:
        raise ValueError(f"invalid source: {value!r}")


def project_exists(project_id: int) -> bool:
    """Return True if ``projects.id`` exists (for FK validation before inserting tasks)."""
    return project_service.project_exists(project_id)


def _row_to_task(row: Any) -> dict[str, Any]:
    d = dict(row)
    return {
        "id": d["id"],
        "project_id": d["project_id"],
        "title": d["title"],
        "description": d["description"],
        "status": d["status"],
        "priority": d["priority"],
        "type": d["type"],
        "source": d["source"],
        "created_at": d["created_at"],
        "updated_at": d["updated_at"],
        "correlation_id": d.get("correlation_id"),
        "created_by": d.get("created_by"),
        "notes": d.get("notes"),
        "requirement_ref": d.get("requirement_ref"),
        "decision_id": d.get("decision_id"),
    }


def create_task(
    project_id: int,
    title: str,
    *,
    description: str | None = None,
    status: str = "pending",
    priority: str = "normal",
    task_type: str = "chore",
    source: str = "manual",
    created_at: str | None = None,
    updated_at: str | None = None,
    correlation_id: str | None = None,
    created_by: str | None = None,
    notes: str | None = None,
    requirement_ref: str | None = None,
    decision_id: int | None = None,
) -> dict[str, Any]:
    _validate_status(status)
    _validate_priority(priority)
    _validate_type(task_type)
    _validate_source(source)
    if created_at is None and updated_at is None:
        now = _iso_now()
        c_at = u_at = now
    else:
        c_at = normalize_timestamp(created_at) if created_at is not None else _iso_now()
        u_at = normalize_timestamp(updated_at) if updated_at is not None else _iso_now()
    with db.connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks (
              project_id, title, description, status, priority, type, source, created_at, updated_at,
              correlation_id, created_by, notes, requirement_ref, decision_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id
            """,
            (
                project_id,
                title,
                description,
                status,
                priority,
                task_type,
                source,
                c_at,
                u_at,
                correlation_id,
                created_by,
                notes,
                requirement_ref,
                decision_id,
            ),
        )
        tid = cur.lastrowid
        conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (tid,)).fetchone()
        assert row is not None
        return _row_to_task(row)


def get_task(task_id: int) -> dict[str, Any] | None:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return _row_to_task(row) if row else None


def list_tasks(
    *,
    project_id: int | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    if status is not None:
        _validate_status(status)
    clauses: list[str] = []
    params: list[Any] = []
    if project_id is not None:
        clauses.append("project_id = ?")
        params.append(project_id)
    if status is not None:
        clauses.append("status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT * FROM tasks {where} ORDER BY id ASC"
    with db.connect() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [_row_to_task(r) for r in rows]


def update_task(
    task_id: int,
    *,
    title: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    task_type: str | None = None,
    correlation_id: str | None = None,
    notes: str | None = None,
) -> dict[str, Any] | None:
    """Update editable fields; only provided keys are changed."""
    existing = get_task(task_id)
    if existing is None:
        return None
    if status is not None:
        _validate_status(status)
    if priority is not None:
        _validate_priority(priority)
    if task_type is not None:
        _validate_type(task_type)
    now = _iso_now()
    fields: list[str] = []
    params: list[Any] = []
    if title is not None:
        fields.append("title = ?")
        params.append(title.strip() if title else "")
    if description is not None:
        fields.append("description = ?")
        params.append(description)
    if priority is not None:
        fields.append("priority = ?")
        params.append(priority)
    if status is not None:
        fields.append("status = ?")
        params.append(status)
    if task_type is not None:
        fields.append("type = ?")
        params.append(task_type)
    if correlation_id is not None:
        fields.append("correlation_id = ?")
        params.append(correlation_id if correlation_id else None)
    if notes is not None:
        fields.append("notes = ?")
        params.append(notes if notes else None)
    if not fields:
        return existing
    fields.append("updated_at = ?")
    params.append(now)
    params.append(task_id)
    sql = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?"
    with db.connect() as conn:
        conn.execute(sql, params)
        conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return _row_to_task(row) if row else None


def delete_task(task_id: int) -> bool:
    """Delete task and its runs (FK order)."""
    with db.connect() as conn:
        conn.execute("DELETE FROM runs WHERE task_id = ?", (task_id,))
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cur.rowcount == 1


def update_status(task_id: int, status: str) -> dict[str, Any] | None:
    _validate_status(status)
    now = _iso_now()
    with db.connect() as conn:
        conn.execute(
            "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, task_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return _row_to_task(row) if row else None


def claim_next_pending(*, project_id: int | None = None) -> dict[str, Any] | None:
    """Atomically pick the next pending task (highest priority, oldest first) and set in_progress."""
    base_where = "status = 'pending'"
    params: list[Any] = []
    if project_id is not None:
        base_where += " AND project_id = ?"
        params.append(project_id)
    order = """
      ORDER BY CASE priority
        WHEN 'urgent' THEN 4
        WHEN 'high' THEN 3
        WHEN 'normal' THEN 2
        WHEN 'low' THEN 1
        ELSE 0
      END DESC,
      created_at ASC
      LIMIT 1
    """
    select_sql = f"SELECT * FROM tasks WHERE {base_where} {order}"
    MAX_RETRIES = 3
    with db.connect() as conn:
        attempt = 0
        while attempt < MAX_RETRIES:
            attempt += 1
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(select_sql, params).fetchone()
            if row is None:
                conn.commit()
                return None
            now = _iso_now()
            cur = conn.execute(
                """
                UPDATE tasks SET status = 'in_progress', updated_at = ?
                WHERE id = ? AND status = 'pending'
                """,
                (now, row["id"]),
            )
            if cur.rowcount != 1:
                conn.rollback()
                continue
            conn.commit()
            fresh = conn.execute("SELECT * FROM tasks WHERE id = ?", (row["id"],)).fetchone()
            assert fresh is not None
            return _row_to_task(fresh)
        raise RuntimeError("Failed to claim task after retries")
