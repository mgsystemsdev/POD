"""
Mirror on-disk Claude project files into SQLite for the task dashboard.

- ``project.md`` → ``blueprints`` (type ``project_md``) — **Blueprints** tab
- ``decisions.md`` → ``decisions`` (file-mirror upsert) — **Decisions** tab
- ``requirements.md`` → ``requirements`` table (``## REQ-...`` sections) — **Requirements** tab
- ``session.md`` / ``sessions.md`` → ``session_logs`` (file-mirror upsert) — **Session Log** tab
- ``.claude/memory/MEMORY.md`` → one ``memory`` row (key ``mirror/memory/MEMORY.md``) — **Memory** tab

Used by ``workers/task_worker.py`` (project.md only) and ``push_claude_artifacts.py``.
"""

from __future__ import annotations

from pathlib import Path

# Dashboard Memory tab: only this file is mirrored (other ``.claude/memory/*.md`` stay local for tools)
MEMORY_FOLDER_SYNC_PREFIX = "mirror/memory/"
MEMORY_DASHBOARD_FILE = "MEMORY.md"

# Removed from decisions/session tables; delete if still present in memory
LEGACY_MEMORY_KEYS = frozenset({"mirror_claude_decisions_md", "mirror_claude_session_md"})


def upsert_file_blueprint_from_disk(
    project_id: int,
    file_path: Path,
    *,
    blueprint_type: str,
    title: str,
    dry_run: bool,
) -> tuple[str, str]:
    """
    Upsert the contents of ``file_path`` into the newest blueprint row for
    ``(project_id, blueprint_type)``, or create one.

    Returns (kind, message) with kind in
    skipped|unchanged|updated|created|error|dry-run.
    """
    import blueprint_service  # noqa: PLC0415

    label = str(file_path)
    if not file_path.is_file():
        return "skipped", f"no {label}"
    try:
        content = file_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        return "error", f"read failed {label}: {exc}"
    if not content:
        return "skipped", f"{label} is empty"

    bt = (blueprint_type or "").strip()
    ti = (title or "").strip()
    if not bt or not ti:
        return "error", "blueprint_type and title are required"

    try:
        rows = blueprint_service.list_by_project(project_id, blueprint_type=bt)
        if dry_run:
            if rows:
                return "dry-run", f"would update blueprint id={rows[0]['id']} ({len(content)} chars) ← {label}"
            return "dry-run", f"would create {bt!r} ({len(content)} chars) ← {label}"
        if rows:
            bid = int(rows[0]["id"])
            if (rows[0].get("content") or "").strip() == content:
                return "unchanged", f"blueprint id={bid} (already matches disk) ← {label}"
            blueprint_service.update(bid, content=content)
            return "updated", f"blueprint id={bid} updated ← {label}"
        blueprint_service.create(project_id, bt, ti, content, version=1)
        return "created", f"created blueprint {bt!r} ← {label}"
    except Exception as exc:
        return "error", f"{type(exc).__name__}: {exc}"


def upsert_decisions_file_from_disk(
    project_id: int,
    file_path: Path,
    *,
    dry_run: bool,
) -> tuple[str, str]:
    """Sync ``.claude/decisions.md`` → decisions table (dashboard Decisions tab)."""
    import decision_service  # noqa: PLC0415

    label = str(file_path)
    if not file_path.is_file():
        return "skipped", f"no {label}"
    try:
        content = file_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        return "error", f"read failed {label}: {exc}"
    if not content:
        return "skipped", f"{label} is empty"

    try:
        if dry_run:
            return "dry-run", f"would upsert decisions file-mirror ({len(content)} chars) ← {label}"
        existing = decision_service.get_file_mirror_decision(project_id)
        if existing and (existing.get("content") or "").strip() == content:
            return "unchanged", f"decisions file-mirror (already matches disk) ← {label}"
        decision_service.upsert_file_mirror_decision(project_id, content)
        return ("updated" if existing else "created"), f"decisions tab ← {label}"
    except Exception as exc:
        return "error", f"{type(exc).__name__}: {exc}"


def upsert_requirements_file_from_disk(
    project_id: int,
    file_path: Path,
    *,
    dry_run: bool,
) -> tuple[str, str]:
    """Parse ``.claude/requirements.md`` (``## REQ-...``) into the ``requirements`` table."""
    import requirement_service  # noqa: PLC0415

    label = str(file_path)
    if not file_path.is_file():
        return "skipped", f"no {label}"
    try:
        content = file_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        return "error", f"read failed {label}: {exc}"

    try:
        parsed = requirement_service.parse_requirements_markdown(content)
        if dry_run:
            return (
                "dry-run",
                f"would sync requirements ({len(parsed)} section(s)) ← {label}",
            )
        kind, msg = requirement_service.replace_from_disk(project_id, content)
        return kind, msg
    except Exception as exc:
        return "error", f"{type(exc).__name__}: {exc}"


def upsert_session_file_from_disk(
    project_id: int,
    file_path: Path,
    *,
    dry_run: bool,
) -> tuple[str, str]:
    """Sync ``.claude/session.md`` (or ``sessions.md``) → session_logs (Session Log tab)."""
    import session_log_service  # noqa: PLC0415

    label = str(file_path)
    if not file_path.is_file():
        return "skipped", f"no {label}"
    try:
        content = file_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        return "error", f"read failed {label}: {exc}"
    if not content:
        return "skipped", f"{label} is empty"

    try:
        if dry_run:
            return "dry-run", f"would upsert session file-mirror ({len(content)} chars) ← {label}"
        existing = session_log_service.get_file_mirror_session(project_id)
        if existing and (existing.get("notes") or "").strip() == content:
            return "unchanged", f"session file-mirror (already matches disk) ← {label}"
        session_log_service.upsert_file_mirror_session(project_id, content)
        return ("updated" if existing else "created"), f"session log tab ← {label}"
    except Exception as exc:
        return "error", f"{type(exc).__name__}: {exc}"


def sync_claude_memory_file(
    project_id: int,
    file_path: Path,
    *,
    dry_run: bool,
) -> tuple[str, str, str]:
    """
    Sync the new single-file memory layout: ``.claude/governance/memory.md`` →
    one ``memory`` row (key ``mirror/memory/MEMORY.md``). Also prunes any other
    ``mirror/memory/*`` rows and legacy ``mirror_claude_*`` keys.

    Returns ``(label, kind, msg)``.
    """
    import memory_service  # noqa: PLC0415

    label = f"memory.md → {MEMORY_FOLDER_SYNC_PREFIX}{MEMORY_DASHBOARD_FILE}"

    if not file_path.is_file():
        return (label, "skipped", f"no {file_path}")
    try:
        content = file_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        return (label, "error", f"read failed: {exc}")
    if not content:
        return (label, "skipped", f"{file_path} is empty")

    if dry_run:
        return (
            label,
            "dry-run",
            f"would set {MEMORY_FOLDER_SYNC_PREFIX}{MEMORY_DASHBOARD_FILE} ({len(content)} chars)",
        )

    # Clean up legacy keys + any stale mirror/memory/* rows (same invariant as folder sync)
    for lk in LEGACY_MEMORY_KEYS:
        memory_service.delete_memory(project_id, lk)
    memory_service.delete_keys_with_prefix(project_id, MEMORY_FOLDER_SYNC_PREFIX)

    key = f"{MEMORY_FOLDER_SYNC_PREFIX}{MEMORY_DASHBOARD_FILE}"
    try:
        memory_service.upsert_memory(project_id, key, content)
        return (label, "updated", f"memory tab ← {key!r}")
    except Exception as exc:
        return (label, "error", f"{type(exc).__name__}: {exc}")


def sync_claude_memory_folder(
    project_id: int,
    memory_dir: Path,
    *,
    dry_run: bool,
) -> list[tuple[str, str, str]]:
    """
    Replace ``mirror/memory/*`` for this project with **only** ``.claude/memory/MEMORY.md``.

    Other ``.claude/memory/*.md`` files are not pushed to SQLite (they remain for local Claude).

    Also removes legacy ``mirror_claude_*`` keys from when decisions/session used Memory.

    Returns a list of ``(label, kind, msg)`` for logging.
    """
    import memory_service  # noqa: PLC0415

    out: list[tuple[str, str, str]] = []

    def _legacy_cleanup() -> None:
        for lk in LEGACY_MEMORY_KEYS:
            if dry_run:
                row = memory_service.get_memory(project_id, lk)
                if row:
                    out.append((lk, "dry-run", f"would delete legacy memory key {lk!r}"))
                continue
            if memory_service.delete_memory(project_id, lk):
                out.append((lk, "deleted", "removed legacy mirror key"))

    _legacy_cleanup()

    memory_md = memory_dir / MEMORY_DASHBOARD_FILE

    if not memory_dir.is_dir():
        if dry_run:
            out.append(("memory/MEMORY.md", "dry-run", "would prune mirror/memory/* (no .claude/memory dir)"))
            return out
        n = memory_service.delete_keys_with_prefix(project_id, MEMORY_FOLDER_SYNC_PREFIX)
        if n:
            out.append(("memory/", "pruned", f"removed {n} mirror/memory/* row(s)"))
        return out

    if dry_run:
        if memory_md.is_file():
            out.append(
                (
                    "memory/MEMORY.md",
                    "dry-run",
                    "would set mirror/memory/MEMORY.md from .claude/memory/MEMORY.md",
                )
            )
        else:
            out.append(
                (
                    "memory/MEMORY.md",
                    "dry-run",
                    "would delete mirror/memory/* (no MEMORY.md)",
                )
            )
        return out

    memory_service.delete_keys_with_prefix(project_id, MEMORY_FOLDER_SYNC_PREFIX)

    label = f"memory/{MEMORY_DASHBOARD_FILE}"
    if not memory_md.is_file():
        out.append((label, "skipped", "no .claude/memory/MEMORY.md"))
        return out

    try:
        content = memory_md.read_text(encoding="utf-8").strip()
    except OSError as exc:
        out.append((label, "error", f"read failed: {exc}"))
        return out
    if not content:
        out.append((label, "skipped", "MEMORY.md is empty"))
        return out

    key = f"{MEMORY_FOLDER_SYNC_PREFIX}{MEMORY_DASHBOARD_FILE}"
    try:
        memory_service.upsert_memory(project_id, key, content)
        out.append((label, "updated", f"memory tab ← {key!r}"))
    except Exception as exc:
        out.append((label, "error", f"{type(exc).__name__}: {exc}"))

    return out
