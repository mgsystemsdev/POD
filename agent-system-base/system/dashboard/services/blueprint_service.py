"""Blueprint CRUD service."""
from __future__ import annotations

from typing import Optional

import db


def list_by_project(
    project_id: int,
    blueprint_type: Optional[str] = None,
) -> list[dict]:
    if blueprint_type is not None:
        with db.get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM blueprints WHERE project_id = ? AND blueprint_type = ? ORDER BY id",
                (project_id, blueprint_type),
            )
            return db.fetchall(cur)
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM blueprints WHERE project_id = ? ORDER BY id",
            (project_id,),
        )
        return db.fetchall(cur)


def get(blueprint_id: int) -> dict | None:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM blueprints WHERE id = ?", (blueprint_id,))
        return db.fetchone(cur)


def create(
    project_id: int,
    blueprint_type: str,
    title: str,
    content: str,
    version: int = 1,
) -> dict:
    if not title:
        raise ValueError("title is required")
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO blueprints (project_id, blueprint_type, title, content, version)
               VALUES (?, ?, ?, ?, ?)""",
            (project_id, blueprint_type, title, content, version),
        )
        row_id = cur.lastrowid
        cur.execute("SELECT * FROM blueprints WHERE id = ?", (row_id,))
        return db.fetchone(cur)


def update(
    blueprint_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    version: Optional[int] = None,
) -> dict | None:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM blueprints WHERE id = ?", (blueprint_id,))
        row = db.fetchone(cur)
        if row is None:
            return None
        new_title = title if title is not None else row["title"]
        new_content = content if content is not None else row["content"]
        new_version = version if version is not None else row["version"]
        cur.execute(
            """UPDATE blueprints SET title = ?, content = ?, version = ?,
               updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now')
               WHERE id = ?""",
            (new_title, new_content, new_version, blueprint_id),
        )
        cur.execute("SELECT * FROM blueprints WHERE id = ?", (blueprint_id,))
        return db.fetchone(cur)


def delete(blueprint_id: int) -> bool:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM blueprints WHERE id = ?", (blueprint_id,))
        return cur.rowcount > 0
