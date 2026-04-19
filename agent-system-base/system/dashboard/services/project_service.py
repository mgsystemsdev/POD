"""Project CRUD service."""
from __future__ import annotations

from typing import Optional

import db


class ProjectSlugConflictError(Exception):
    pass


def list_projects() -> list[dict]:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM projects ORDER BY id")
        return db.fetchall(cur)


def get_project(project_id: int) -> dict | None:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        return db.fetchone(cur)


def create_project(
    name: str,
    slug: str,
    root_path: Optional[str] = None,
) -> dict:
    if not name or not slug:
        raise ValueError("name and slug are required")
    with db.get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO projects (name, slug, root_path) VALUES (?, ?, ?)",
                (name, slug, root_path),
            )
            row_id = cur.lastrowid
        except Exception as exc:
            if "UNIQUE" in str(exc).upper():
                raise ProjectSlugConflictError(f"Slug {slug!r} already exists") from exc
            raise
        cur.execute("SELECT * FROM projects WHERE id = ?", (row_id,))
        return db.fetchone(cur)


def upsert_project(
    name: str,
    slug: str,
    root_path: Optional[str] = None,
) -> tuple[dict, bool]:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM projects WHERE slug = ?", (slug,))
        existing = db.fetchone(cur)
        if existing:
            cur.execute(
                "UPDATE projects SET name = ?, root_path = ? WHERE slug = ?",
                (name, root_path, slug),
            )
            cur.execute("SELECT * FROM projects WHERE slug = ?", (slug,))
            return db.fetchone(cur), False
        cur.execute(
            "INSERT INTO projects (name, slug, root_path) VALUES (?, ?, ?)",
            (name, slug, root_path),
        )
        row_id = cur.lastrowid
        cur.execute("SELECT * FROM projects WHERE id = ?", (row_id,))
        return db.fetchone(cur), True


def update_project(
    project_id: int,
    name: Optional[str] = None,
    root_path: Optional[str] = None,
) -> dict | None:
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = db.fetchone(cur)
        if row is None:
            return None
        new_name = name if name is not None else row["name"]
        new_root = root_path if root_path is not None else row["root_path"]
        cur.execute(
            "UPDATE projects SET name = ?, root_path = ? WHERE id = ?",
            (new_name, new_root, project_id),
        )
        cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        return db.fetchone(cur)
