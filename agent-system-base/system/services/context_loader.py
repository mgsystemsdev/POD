from __future__ import annotations

from pathlib import Path
from typing import Any

import project_service

# Sections to extract from AGENTS.md for prompt injection (~400 tokens max).
_RULES_SECTIONS = ("Agent Roster", "Tool Permissions", "Output Format")
_FALLBACK_AGENTS_MD = Path.home() / "agents" / "agent-system-base" / "AGENTS.md"


def _extract_sections(text: str, section_names: tuple[str, ...]) -> str:
    """
    Extract named ## sections from a markdown document.
    Returns only the lines belonging to those sections (up to the next ## heading).
    """
    lines = text.splitlines()
    captured: list[str] = []
    capturing = False
    for line in lines:
        if line.startswith("## "):
            heading = line[3:].strip()
            capturing = any(s.lower() in heading.lower() for s in section_names)
            if capturing:
                captured.append(line)
        elif capturing:
            captured.append(line)
    return "\n".join(captured).strip()


def load_rules_context(project_root: Path | None) -> str | None:
    """
    Return a condensed subset of AGENTS.md (Agent Roster, Tool Permissions, Output Format).

    Searches in order:
      1. <project_root>/AGENTS.md
      2. ~/agents/agent-system-base/AGENTS.md  (global fallback)

    Returns None if neither file is found — callers treat this as "no rules available".
    """
    candidates: list[Path] = []
    if project_root:
        candidates.append(Path(project_root) / "AGENTS.md")
    candidates.append(_FALLBACK_AGENTS_MD)

    for path in candidates:
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
                extracted = _extract_sections(text, _RULES_SECTIONS)
                return extracted if extracted else text[:2000]
            except OSError:
                continue
    return None


def load_project_context(
    *,
    project_id: int | None = None,
    slug: str | None = None,
) -> dict[str, Any]:
    """
    Resolve the registry row and optional on-disk root for a project.

    Exactly one of ``project_id`` or ``slug`` must be provided.

    Returns a dict with:
      - ``project``, ``root``, ``root_exists`` (as before)
      - ``project_md``: first 12k chars of ``.claude/project.md`` when present
      - ``session_log``: latest ``session_logs`` row or None
      - ``recent_decisions``: up to 5 decisions for this project
      - ``latest_blueprints``: up to 1 newest blueprint row
    """
    if (project_id is None) == (slug is None):
        raise ValueError("exactly one of project_id or slug must be provided")

    if project_id is not None:
        row = project_service.get_project(project_id)
    else:
        assert slug is not None
        row = project_service.get_project_by_slug(slug)

    if row is None:
        raise LookupError(f"project not found: {project_id!r}" if project_id is not None else f"slug={slug!r}")

    raw = row.get("root_path")
    root: Path | None = None
    root_exists: bool | None = None
    if raw and isinstance(raw, str) and raw.strip():
        root = Path(raw.strip()).expanduser().resolve()
        root_exists = root.is_dir()

    pid = int(row["id"])
    project_md: str | None = None
    if root is not None and root_exists:
        pm = root / ".claude" / "project.md"
        if pm.is_file():
            try:
                project_md = pm.read_text(encoding="utf-8")[:12000]
            except OSError:
                project_md = None

    session_log: dict[str, Any] | None = None
    recent_decisions: list[dict[str, Any]] = []
    latest_blueprints: list[dict[str, Any]] = []
    try:
        import blueprint_service  # noqa: PLC0415
        import decision_service  # noqa: PLC0415
        import session_log_service  # noqa: PLC0415

        session_log = session_log_service.get_latest(pid)
        all_dec = decision_service.list_decisions(project_id=pid)
        recent_decisions = all_dec[-5:] if len(all_dec) > 5 else list(all_dec)
        latest_blueprints = blueprint_service.list_by_project(pid)[:1]
    except Exception:
        pass

    return {
        "project": row,
        "root": root,
        "root_exists": root_exists,
        "project_md": project_md,
        "session_log": session_log,
        "recent_decisions": recent_decisions,
        "latest_blueprints": latest_blueprints,
    }
