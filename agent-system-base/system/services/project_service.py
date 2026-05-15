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


class ProjectDeleteBlockedError(Exception):
    """Raised when ``delete_project`` cannot run because child rows exist."""

    def __init__(self, counts: dict[str, int]):
        self.counts = {k: v for k, v in counts.items() if v > 0}
        parts = [f"{k}: {v}" for k, v in sorted(self.counts.items())]
        msg = "Cannot delete project while related data exists: " + (
            "; ".join(parts) if parts else "related data exists"
        )
        super().__init__(msg)


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


def _safe_count(conn: Any, sql: str, project_id: int) -> int:
    """Return COUNT or 0 if the table does not exist (migration not applied)."""
    try:
        row = conn.execute(sql, (project_id,)).fetchone()
        if row is None:
            return 0
        return int(row[0])
    except Exception as exc:
        msg = str(exc).lower()
        if "no such table" in msg or "does not exist" in msg:
            return 0
        raise


_CHILD_COUNT_SQL: list[tuple[str, str]] = [
    ("tasks", "SELECT COUNT(*) FROM tasks WHERE project_id = ?"),
    ("blueprints", "SELECT COUNT(*) FROM blueprints WHERE project_id = ?"),
    ("session_logs", "SELECT COUNT(*) FROM session_logs WHERE project_id = ?"),
    ("memory", "SELECT COUNT(*) FROM memory WHERE project_id = ?"),
    ("decisions", "SELECT COUNT(*) FROM decisions WHERE project_id = ?"),
    (
        "auxiliary_agent_outputs",
        "SELECT COUNT(*) FROM auxiliary_agent_outputs WHERE project_id = ?",
    ),
    (
        "proposed_actions",
        "SELECT COUNT(*) FROM proposed_actions WHERE project_id = ?",
    ),
    ("backlog", "SELECT COUNT(*) FROM backlog WHERE project_id = ?"),
    ("approvals", "SELECT COUNT(*) FROM approvals WHERE project_id = ?"),
    ("validations", "SELECT COUNT(*) FROM validations WHERE project_id = ?"),
    ("security_findings", "SELECT COUNT(*) FROM security_findings WHERE project_id = ?"),
    ("db_recommendations", "SELECT COUNT(*) FROM db_recommendations WHERE project_id = ?"),
    (
        "adversarial_critiques",
        "SELECT COUNT(*) FROM adversarial_critiques WHERE project_id = ?",
    ),
]


def project_child_counts(project_id: int) -> dict[str, int]:
    """Count rows referencing ``project_id`` in known dependent tables."""
    out: dict[str, int] = {}
    with db.connect() as conn:
        for label, sql in _CHILD_COUNT_SQL:
            out[label] = _safe_count(conn, sql, project_id)
    return out


def rename_project_slug(project_id: int, new_slug: str) -> dict[str, Any]:
    """Change ``slug`` for an existing project; must stay unique."""
    existing = get_project(project_id)
    if existing is None:
        raise LookupError("project not found")
    _validate_slug(new_slug)
    if existing["slug"] == new_slug:
        return existing
    other = get_project_by_slug(new_slug)
    if other is not None and other["id"] != project_id:
        raise ProjectSlugConflictError("A project with this slug already exists")
    now = _iso_now()
    with db.connect() as conn:
        try:
            conn.execute(
                "UPDATE projects SET slug = ?, updated_at = ? WHERE id = ?",
                (new_slug, now, project_id),
            )
            conn.commit()
        except _IntegrityErrors as exc:
            if "slug" in str(exc).lower():
                raise ProjectSlugConflictError(
                    "A project with this slug already exists"
                ) from exc
            raise
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        assert row is not None
        return _row_to_project(row)


def delete_project(project_id: int) -> bool:
    """Delete a project if it has no dependent rows. Returns False if project missing."""
    if get_project(project_id) is None:
        return False
    with db.connect() as conn:
        counts: dict[str, int] = {}
        for label, sql in _CHILD_COUNT_SQL:
            counts[label] = _safe_count(conn, sql, project_id)
        blocked = {k: v for k, v in counts.items() if v > 0}
        if blocked:
            raise ProjectDeleteBlockedError(blocked)
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
    return True


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
