from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import db
import project_service


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_blueprint(row: Any) -> dict[str, Any]:
    d = dict(row)
    return {
        "id": d["id"],
        "project_id": d["project_id"],
        "type": d["type"],
        "title": d["title"],
        "content": d["content"],
        "version": d["version"],
        "created_at": d["created_at"],
        "updated_at": d["updated_at"],
    }


def create(
    project_id: int,
    blueprint_type: str,
    title: str,
    content: str,
    *,
    version: int = 1,
) -> dict[str, Any]:
    if not project_service.project_exists(project_id):
        raise ValueError(f"unknown project_id: {project_id}")
    t = (blueprint_type or "").strip()
    ti = (title or "").strip()
    c = (content or "").strip()
    if not t:
        raise ValueError("type is required")
    if not ti:
        raise ValueError("title is required")
    if not c:
        raise ValueError("content is required")
    now = _iso_now()
    with db.connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO blueprints (project_id, type, title, content, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id
            """,
            (project_id, t, ti, c, int(version), now, now),
        )
        bid = cur.lastrowid
        conn.commit()
        row = conn.execute("SELECT * FROM blueprints WHERE id = ?", (bid,)).fetchone()
        assert row is not None
        return _row_to_blueprint(row)


def get(blueprint_id: int) -> dict[str, Any] | None:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM blueprints WHERE id = ?", (blueprint_id,)).fetchone()
        return _row_to_blueprint(row) if row else None


def list_by_project(project_id: int, *, blueprint_type: str | None = None) -> list[dict[str, Any]]:
    with db.connect() as conn:
        if blueprint_type is not None and str(blueprint_type).strip():
            rows = conn.execute(
                """
                SELECT * FROM blueprints
                WHERE project_id = ? AND type = ?
                ORDER BY updated_at DESC, id DESC
                """,
                (project_id, str(blueprint_type).strip()),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM blueprints
                WHERE project_id = ?
                ORDER BY updated_at DESC, id DESC
                """,
                (project_id,),
            ).fetchall()
        return [_row_to_blueprint(r) for r in rows]


def update(
    blueprint_id: int,
    *,
    title: str | None = None,
    content: str | None = None,
    version: int | None = None,
) -> dict[str, Any] | None:
    existing = get(blueprint_id)
    if existing is None:
        return None
    now = _iso_now()
    fields: list[str] = []
    params: list[Any] = []
    if title is not None:
        s = title.strip()
        if not s:
            raise ValueError("title cannot be empty")
        fields.append("title = ?")
        params.append(s)
    if content is not None:
        s = content.strip()
        if not s:
            raise ValueError("content cannot be empty")
        fields.append("content = ?")
        params.append(s)
    if version is not None:
        fields.append("version = ?")
        params.append(int(version))
    if not fields:
        return existing
    fields.append("updated_at = ?")
    params.append(now)
    params.append(blueprint_id)
    sql = f"UPDATE blueprints SET {', '.join(fields)} WHERE id = ?"
    with db.connect() as conn:
        conn.execute(sql, params)
        conn.commit()
        row = conn.execute("SELECT * FROM blueprints WHERE id = ?", (blueprint_id,)).fetchone()
        return _row_to_blueprint(row) if row else None


def delete(blueprint_id: int) -> bool:
    with db.connect() as conn:
        cur = conn.execute("DELETE FROM blueprints WHERE id = ?", (blueprint_id,))
        conn.commit()
        return cur.rowcount == 1
