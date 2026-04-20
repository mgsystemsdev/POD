from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import db
import project_service

_ALLOWED_STATUS = frozenset({"draft", "active", "done", "deferred"})

_SECTION = re.compile(r"^##\s+(REQ-[A-Za-z0-9.-]+)\s*(.*?)\s*$", re.MULTILINE)
_STATUS_LINE = re.compile(r"^status:\s*([\w-]+)\s*$", re.IGNORECASE)


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_ref(ref: str) -> str:
    r = (ref or "").strip()
    m = re.match(r"(?i)^REQ-(.+)$", r)
    if m:
        return "REQ-" + m.group(1).strip()
    return r


def _normalize_status(raw: str) -> str:
    s = (raw or "").strip().lower()
    return s if s in _ALLOWED_STATUS else "draft"


def _strip_status_prefix(body: str) -> tuple[str, str]:
    """Return (status, body) with optional leading ``Status:`` line removed from body."""
    b = (body or "").strip()
    if not b:
        return "draft", ""
    lines = b.splitlines()
    m0 = _STATUS_LINE.match(lines[0].strip()) if lines else None
    if m0:
        st = _normalize_status(m0.group(1))
        rest = "\n".join(lines[1:]).strip()
        return st, rest
    return "draft", b


def parse_requirements_markdown(content: str) -> list[dict[str, str]]:
    """
    Parse ``.claude/requirements.md`` — one requirement per ``## REQ-...`` section.

    Optional first line in section: ``Status: draft|active|done|deferred``.
    """
    text = (content or "").strip()
    if not text:
        return []
    matches = list(_SECTION.finditer(text))
    if not matches:
        return []
    out: list[dict[str, str]] = []
    for i, m in enumerate(matches):
        ref = normalize_ref(m.group(1))
        inline_title = (m.group(2) or "").strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        status, body = _strip_status_prefix(block)
        title = inline_title or ref
        out.append({"ref": ref, "title": title, "body": body, "status": status})
    return out


def _row_to_dict(row: Any) -> dict[str, Any]:
    d = dict(row)
    ff = d.get("from_file")
    if isinstance(ff, bool):
        d["from_file"] = 1 if ff else 0
    return {
        "id": d["id"],
        "project_id": d["project_id"],
        "ref": d["ref"],
        "title": d["title"],
        "body": d.get("body"),
        "status": d["status"],
        "from_file": int(d["from_file"]) if d.get("from_file") is not None else 1,
        "created_at": d["created_at"],
        "updated_at": d["updated_at"],
    }


def list_by_project(project_id: int) -> list[dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM requirements
            WHERE project_id = ?
            ORDER BY ref ASC, id ASC
            """,
            (project_id,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


def add_requirement(
    project_id: int,
    ref: str,
    title: str,
    *,
    body: str | None = None,
    status: str = "draft",
) -> dict[str, Any]:
    """Create a dashboard-only row (``from_file`` = 0). Not overwritten by empty file sync."""
    if not project_service.project_exists(project_id):
        raise ValueError(f"unknown project_id: {project_id}")
    r = normalize_ref(ref)
    if not r or not r.upper().startswith("REQ-"):
        raise ValueError("ref must look like REQ-###")
    t = (title or "").strip()
    if not t:
        raise ValueError("title is required")
    st = _normalize_status(status)
    now = _iso_now()
    b = (body or "").strip() if body is not None else ""
    with db.connect() as conn:
        row = conn.execute(
            "SELECT id FROM requirements WHERE project_id = ? AND ref = ?",
            (project_id, r),
        ).fetchone()
        if row:
            raise ValueError(f"requirement {r!r} already exists for this project")
        cur = conn.execute(
            """
            INSERT INTO requirements (project_id, ref, title, body, status, from_file, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id
            """,
            (project_id, r, t, b or None, st, False, now, now),
        )
        rid = cur.lastrowid
        conn.commit()
        out = conn.execute("SELECT * FROM requirements WHERE id = ?", (rid,)).fetchone()
        assert out is not None
        return _row_to_dict(out)


def replace_from_disk(project_id: int, markdown: str) -> tuple[str, str]:
    """
    Parse markdown and upsert file-backed rows (``from_file`` = 1).
    Removes file-backed rows whose ``ref`` is absent from the file.
    Returns (kind, message) for logging.
    """
    if not project_service.project_exists(project_id):
        raise ValueError(f"unknown project_id: {project_id}")
    parsed = parse_requirements_markdown(markdown)
    refs = [p["ref"] for p in parsed]
    now = _iso_now()

    with db.connect() as conn:
        if refs:
            placeholders = ",".join("?" * len(refs))
            conn.execute(
                f"""
                DELETE FROM requirements
                WHERE project_id = ? AND from_file = ? AND ref NOT IN ({placeholders})
                """,
                (project_id, True, *refs),
            )
        else:
            conn.execute(
                "DELETE FROM requirements WHERE project_id = ? AND from_file = ?",
                (project_id, True),
            )

        for p in parsed:
            row = conn.execute(
                "SELECT id, from_file FROM requirements WHERE project_id = ? AND ref = ?",
                (project_id, p["ref"]),
            ).fetchone()
            body = p.get("body") or ""
            body_val = body.strip() if body.strip() else None
            if row:
                conn.execute(
                    """
                    UPDATE requirements
                    SET title = ?, body = ?, status = ?, from_file = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (p["title"], body_val, p["status"], True, now, int(row["id"])),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO requirements (project_id, ref, title, body, status, from_file, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (project_id, p["ref"], p["title"], body_val, p["status"], True, now, now),
                )
        conn.commit()

    n = len(parsed)
    return "updated", f"requirements: {n} row(s) from disk ← project_id={project_id}"
