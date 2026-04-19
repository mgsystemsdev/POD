from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import db
import project_service


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_memory(row: Any) -> dict[str, Any]:
    d = dict(row)
    return {
        "id": d["id"],
        "project_id": d["project_id"],
        "key": d["key"],
        "value": d["value"],
        "updated_at": d["updated_at"],
        "created_by": d.get("created_by"),
        "write_reason": d.get("write_reason"),
    }


def _validate_key_value(key: str, value: str) -> tuple[str, str]:
    k = key.strip() if isinstance(key, str) else ""
    v = value.strip() if isinstance(value, str) else ""
    if not k:
        raise ValueError("key is required")
    if not v:
        raise ValueError("value is required")
    return k, v


def upsert_memory(
    project_id: int,
    key: str,
    value: str,
    *,
    created_by: str | None = None,
    write_reason: str | None = None,
) -> dict[str, Any]:
    """Insert or replace the row for (project_id, key); ``updated_at`` is always set to now."""
    if not project_service.project_exists(project_id):
        raise ValueError(f"unknown project_id: {project_id}")
    k, v = _validate_key_value(key, value)
    now = _iso_now()
    with db.connect() as conn:
        conn.execute(
            """
            INSERT INTO memory (project_id, key, value, updated_at, created_by, write_reason)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, key) DO UPDATE SET
              value = excluded.value,
              updated_at = excluded.updated_at,
              created_by = excluded.created_by,
              write_reason = excluded.write_reason
            """,
            (project_id, k, v, now, created_by, write_reason),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM memory WHERE project_id = ? AND key = ?",
            (project_id, k),
        ).fetchone()
        assert row is not None
        return _row_to_memory(row)


def get_memory(project_id: int, key: str) -> dict[str, Any] | None:
    k = key.strip() if isinstance(key, str) else ""
    if not k:
        raise ValueError("key is required")
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM memory WHERE project_id = ? AND key = ?",
            (project_id, k),
        ).fetchone()
        return _row_to_memory(row) if row else None


def list_memory(*, project_id: int | None = None) -> list[dict[str, Any]]:
    """Return memory rows ordered by ``project_id`` ASC, ``key`` ASC."""
    with db.connect() as conn:
        if project_id is not None:
            rows = conn.execute(
                """
                SELECT * FROM memory
                WHERE project_id = ?
                ORDER BY key ASC
                """,
                (project_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM memory ORDER BY project_id ASC, key ASC"
            ).fetchall()
        return [_row_to_memory(r) for r in rows]


def delete_memory(project_id: int, key: str) -> bool:
    """Delete one row. Returns True if a row was removed."""
    k = key.strip() if isinstance(key, str) else ""
    if not k:
        raise ValueError("key is required")
    with db.connect() as conn:
        cur = conn.execute(
            "DELETE FROM memory WHERE project_id = ? AND key = ?",
            (project_id, k),
        )
        conn.commit()
        return cur.rowcount > 0


def delete_keys_with_prefix(project_id: int, prefix: str) -> int:
    """Delete all rows for this project whose key starts with ``prefix``."""
    p = prefix if isinstance(prefix, str) else ""
    if not p:
        raise ValueError("prefix is required")
    with db.connect() as conn:
        cur = conn.execute(
            "DELETE FROM memory WHERE project_id = ? AND key LIKE ?",
            (project_id, p + "%"),
        )
        conn.commit()
        return int(cur.rowcount)
