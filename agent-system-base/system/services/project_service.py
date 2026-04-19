from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from typing import Any

try:
    import psycopg2

    _IntegrityErrors = (sqlite3.IntegrityError, psycopg2.IntegrityError)
except ImportError:
    _IntegrityErrors = (sqlite3.IntegrityError,)

import db


class ProjectSlugConflictError(ValueError):
    """Raised when ``create_project`` uses a slug that already exists."""

    pass


_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}$")


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _validate_slug(slug: str) -> None:
    if not slug or not isinstance(slug, str):
        raise ValueError("slug is required")
    s = slug.strip().lower()
    if s != slug:
        raise ValueError("slug must be lowercase with no surrounding whitespace")
    if not _SLUG_RE.match(s):
        raise ValueError(
            "slug must match ^[a-z0-9][a-z0-9_-]{0,62}$ (lowercase letters, digits, _ and -)"
        )


def _row_to_project(row: Any) -> dict[str, Any]:
    d = dict(row)
    return {
        "id": d["id"],
        "name": d["name"],
        "slug": d["slug"],
        "root_path": d.get("root_path"),
        "created_at": d["created_at"],
        "updated_at": d["updated_at"],
    }


def project_exists(project_id: int) -> bool:
    """Return True if ``projects.id`` exists."""
    with db.connect() as conn:
        row = conn.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone()
        return row is not None


def list_projects() -> list[dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY id ASC").fetchall()
        return [_row_to_project(r) for r in rows]


def get_project(project_id: int) -> dict[str, Any] | None:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return _row_to_project(row) if row else None


def get_project_by_slug(slug: str) -> dict[str, Any] | None:
    _validate_slug(slug)
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM projects WHERE slug = ?", (slug,)).fetchone()
        return _row_to_project(row) if row else None


def create_project(
    name: str,
    slug: str,
    *,
    root_path: str | None = None,
) -> dict[str, Any]:
    if not name or not str(name).strip():
        raise ValueError("name is required")
    _validate_slug(slug)
    now = _iso_now()
    with db.connect() as conn:
        try:
            cur = conn.execute(
                """
                INSERT INTO projects (name, slug, root_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?) RETURNING id
                """,
                (name.strip(), slug, root_path, now, now),
            )
        except _IntegrityErrors as exc:
            if "slug" in str(exc).lower():
                raise ProjectSlugConflictError(
                    "A project with this slug already exists"
                ) from exc
            raise
        pid = cur.lastrowid
        conn.commit()
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
        assert row is not None
        return _row_to_project(row)


def upsert_project(
    name: str,
    slug: str,
    *,
    root_path: str | None = None,
) -> tuple[dict[str, Any], bool]:
    """Insert or, if ``slug`` exists, update ``name`` and ``root_path``.

    Returns ``(project, created)`` where ``created`` is True on insert.
    """
    if not name or not str(name).strip():
        raise ValueError("name is required")
    _validate_slug(slug)
    n = str(name).strip()
    existing = get_project_by_slug(slug)
    if existing:
        updated = update_project(existing["id"], name=n, root_path=root_path)
        assert updated is not None
        return updated, False
    row = create_project(n, slug, root_path=root_path)
    return row, True


def update_project(
    project_id: int,
    *,
    name: str | None = None,
    root_path: str | None = None,
) -> dict[str, Any] | None:
    """Update display name and/or root_path."""
    existing = get_project(project_id)
    if existing is None:
        return None
    parts: list[str] = []
    params: list[Any] = []
    if name is not None:
        n = str(name).strip()
        if not n:
            raise ValueError("name cannot be empty")
        parts.append("name = ?")
        params.append(n)
    if root_path is not None:
        parts.append("root_path = ?")
        params.append(root_path)
    if not parts:
        return existing
    now = _iso_now()
    parts.append("updated_at = ?")
    params.append(now)
    params.append(project_id)
    sql = f"UPDATE projects SET {', '.join(parts)} WHERE id = ?"
    with db.connect() as conn:
        conn.execute(sql, params)
        conn.commit()
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return _row_to_project(row) if row else None


def set_project_root(project_id: int, root_path: str | None) -> dict[str, Any] | None:
    """Set or clear the on-disk root path for context loading."""
    now = _iso_now()
    with db.connect() as conn:
        cur = conn.execute(
            "UPDATE projects SET root_path = ?, updated_at = ? WHERE id = ?",
            (root_path, now, project_id),
        )
        if cur.rowcount != 1:
            conn.commit()
            return None
        conn.commit()
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return _row_to_project(row) if row else None
