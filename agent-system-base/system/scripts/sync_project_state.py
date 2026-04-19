#!/usr/bin/env python3
"""
agents pull  —  Railway → local .claude/

Railway Postgres is the single source of truth. This script overwrites every
local file under ``.claude/`` with the current Railway state, rendered as
human/Claude-readable markdown (plus ``tasks.json``). Run it at the start of
any session, before editing, or on a cron.

Layout written (identical to ``agents init`` scaffold):

  .claude/
  ├── config.json                         (unchanged — creds only)
  ├── pipeline/
  │   ├── tasks.json                      → Tasks
  │   ├── blueprints.md                   → Blueprints
  │   ├── session_log.md                  → Session Log
  │   └── execution_trace.md              → Execution Trace  (read-only data)
  ├── governance/
  │   ├── decisions.md                    → Decisions
  │   ├── memory.md                       → Memory
  │   ├── approvals.md                    → Approvals        (read-only data)
  │   ├── backlog.md                      → Backlog
  │   └── audit_trail.md                  → Audit Trail      (read-only data)
  └── specialists/
      ├── strategist.md                   → Strategist
      ├── system_design.md                → System Design
      ├── backend_spec.md                 → Backend Spec
      ├── db_spec.md                      → DB Spec
      ├── schema_spec.md                  → Schema Spec
      ├── ui_spec.md                      → UI Spec
      └── senior_dev.md                   → Senior Dev

Pull is **silent overwrite** (Option A) unless ``--dry-run``. On success writes
``.claude/sync_state.json`` (``last_pull_at``, ``last_pull_ok``, ``pull_errors``).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

try:
    import requests
except ImportError:
    print("error: `requests` not installed. pip install requests", file=sys.stderr)
    sys.exit(1)

import agents_cli_config as acfg

# ── Tab → filename registry (single source of truth for this script) ──────────

SPECIALIST_ROLES = [
    "strategist",
    "system_design",
    "backend_spec",
    "db_spec",
    "schema_spec",
    "ui_spec",
    "senior_dev",
]

READONLY_TABS = {"execution_trace", "approvals", "audit_trail"}


# ── HTTP ──────────────────────────────────────────────────────────────────────


def _get(url: str, headers: dict[str, str]) -> Any:
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def _fetch_probe(
    api_url: str, endpoint: str, headers: dict[str, str], label: str
) -> tuple[Any | None, str | None]:
    """Return (json_or_none, error_message)."""
    url = f"{api_url}{endpoint}"
    try:
        data = _get(url, headers)
        return data, None
    except requests.RequestException as e:
        return None, f"{label}: {e}"


# ── Formatting helpers ────────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _header(title: str, note: str = "") -> str:
    lines = [
        f"# {title}",
        "",
        f"<!-- Synced from Railway at {_now_iso()} -->",
        "<!-- SOURCE OF TRUTH: Postgres. This file is a read-only cache; edits are overwritten on next `agents pull`. -->",
    ]
    if note:
        lines.extend(["", f"> {note}"])
    lines.append("")
    return "\n".join(lines)


def _empty_body(what: str) -> str:
    return f"_No {what} yet._\n"


# ── Renderers (Railway JSON → markdown) ───────────────────────────────────────


def render_blueprints(rows: list[dict]) -> str:
    body = _header("Blueprints")
    if not rows:
        return body + _empty_body("blueprints")
    parts = [body]
    for r in rows:
        parts.append(
            f"## {r.get('title') or '(untitled)'}  "
            f"_[#{r.get('id')} · {r.get('type')} · v{r.get('version', 1)}]_\n"
        )
        if r.get("created_by"):
            parts.append(f"_by {r['created_by']} — {r.get('created_at', '')[:19].replace('T', ' ')}_\n")
        parts.append((r.get("content") or "").strip() + "\n")
        parts.append("\n---\n\n")
    return "".join(parts)


def render_session_log(rows: list[dict]) -> str:
    body = _header("Session Log")
    if not rows:
        return body + _empty_body("session entries")
    parts = [body]
    for r in rows:
        date = r.get("session_date") or r.get("created_at", "")[:10]
        agent = r.get("agent") or "—"
        parts.append(f"## {date} — {agent}  _[#{r.get('id')}]_\n")
        for label, key in (
            ("Scope", "scope_active"),
            ("Completed", "tasks_completed"),
            ("Next", "next_task"),
            ("Git", "git_state"),
            ("Open issues", "open_issues"),
            ("Notes", "notes"),
        ):
            v = (r.get(key) or "").strip()
            if v:
                parts.append(f"**{label}:** {v}\n\n")
        parts.append("---\n\n")
    return "".join(parts)


def render_execution_trace(rows: list[dict]) -> str:
    body = _header(
        "Execution Trace",
        "Auto-written by the task worker. Cannot be authored locally.",
    )
    if not rows:
        return body + _empty_body("trace entries")
    lines = [body, "| Time | Agent | Action | Result | Error |", "|---|---|---|---|---|"]
    for r in rows:
        ts = (r.get("timestamp") or "")[:19].replace("T", " ")
        lines.append(
            f"| {ts} "
            f"| {r.get('agent_role') or ''} "
            f"| {(r.get('action') or '').replace('|', '\\|')} "
            f"| {(r.get('result') or '').replace('|', '\\|')} "
            f"| {(r.get('error_message') or '').replace('|', '\\|')} |"
        )
    return "\n".join(lines) + "\n"


def render_decisions(rows: list[dict]) -> str:
    body = _header("Decisions")
    if not rows:
        return body + _empty_body("decisions")
    parts = [body]
    for r in rows:
        date = (r.get("created_at") or "")[:10]
        parts.append(f"## {r.get('title') or '(untitled)'}  _[#{r.get('id')} · {date}]_\n")
        if r.get("created_by"):
            parts.append(f"_by {r['created_by']}_\n\n")
        parts.append((r.get("content") or "").strip() + "\n\n---\n\n")
    return "".join(parts)


def render_memory(rows: list[dict]) -> str:
    body = _header("Memory")
    if not rows:
        return body + _empty_body("memory entries")
    parts = [body]
    for r in rows:
        key = r.get("key") or "(no key)"
        parts.append(f"## `{key}`\n")
        v = (r.get("value") or "").strip()
        if "\n" in v or len(v) > 120:
            parts.append("```\n" + v + "\n```\n\n")
        else:
            parts.append(v + "\n\n")
    return "".join(parts)


def render_approvals(rows: list[dict]) -> str:
    body = _header(
        "Approvals",
        "Written when a human operator approves or rejects an entity in the dashboard.",
    )
    if not rows:
        return body + _empty_body("approvals")
    lines = [body, "| When | Entity | Decision | Approver | Reason |", "|---|---|---|---|---|"]
    for r in rows:
        when = (r.get("created_at") or "")[:19].replace("T", " ")
        lines.append(
            f"| {when} "
            f"| {r.get('entity_type')} #{r.get('entity_id')} "
            f"| **{r.get('decision')}** "
            f"| {r.get('approver_role') or ''} "
            f"| {(r.get('reason') or '').replace('|', '\\|')} |"
        )
    return "\n".join(lines) + "\n"


def render_backlog(rows: list[dict]) -> str:
    # Sentinel row holds full ``governance/backlog.md`` from ``agents push``; show separately.
    cli_mirror_title = "__agents_cli_backlog_mirror__"
    mirror = next((r for r in rows if (r.get("title") or "") == cli_mirror_title), None)
    display = [r for r in rows if (r.get("title") or "") != cli_mirror_title]

    body = _header("Backlog")
    if not display and not mirror:
        return body + _empty_body("backlog items")
    parts = [body]
    for r in display:
        status = r.get("status") or "backlog"
        parts.append(
            f"## {r.get('title') or '(untitled)'}  _[#{r.get('id')} · {status}]_\n"
        )
        if r.get("submitted_by"):
            parts.append(f"_submitted by {r['submitted_by']}_\n\n")
        desc = (r.get("description") or "").strip()
        if desc:
            parts.append(desc + "\n\n")
        parts.append("---\n\n")
    if mirror and (mirror.get("description") or "").strip():
        parts.append("## CLI backlog mirror (agents push)\n\n")
        parts.append((mirror.get("description") or "").strip() + "\n\n")
    return "".join(parts)


def render_audit_trail(rows: list[dict] | None) -> str:
    body = _header(
        "Audit Trail",
        "No dedicated endpoint yet. When available, this file will list every state-changing API call.",
    )
    if not rows:
        return body + _empty_body("audit entries")
    lines = [body, "| When | Actor | Action | Target |", "|---|---|---|---|"]
    for r in rows:
        lines.append(
            f"| {(r.get('timestamp') or '')[:19].replace('T', ' ')} "
            f"| {r.get('actor') or ''} "
            f"| {r.get('action') or ''} "
            f"| {r.get('target') or ''} |"
        )
    return "\n".join(lines) + "\n"


def render_specialist(role: str, rows: list[dict]) -> str:
    body = _header(role.replace("_", " ").title())
    if not rows:
        return body + _empty_body(f"{role} outputs")
    parts = [body]
    for r in rows:
        status = r.get("status") or "pending"
        parts.append(f"## Output #{r.get('id')}  _[{status}]_\n")
        meta_bits = []
        if r.get("target_core_agent"):
            meta_bits.append(f"→ {r['target_core_agent']}")
        if r.get("related_requirement_ref"):
            meta_bits.append(r["related_requirement_ref"])
        if r.get("created_at"):
            meta_bits.append(r["created_at"][:19].replace("T", " "))
        if meta_bits:
            parts.append("_" + " · ".join(meta_bits) + "_\n\n")
        parts.append((r.get("content") or "").strip() + "\n\n---\n\n")
    return "".join(parts)


# ── Write helpers ─────────────────────────────────────────────────────────────


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  ✓ {path}")


def _payload_size(data: Any) -> int:
    try:
        return len(json.dumps(data, ensure_ascii=False))
    except (TypeError, ValueError):
        return 0


def _sync_impl(*, dry_run: bool) -> int:
    cwd = Path.cwd()
    cfg = acfg.load_config_file(cwd=cwd)
    project_id = acfg.require_project_id(cfg)
    api_url = acfg.resolve_api_url(cfg, cwd=cwd)
    headers = acfg.api_headers(cfg)

    root = Path(".claude")
    pipeline = root / "pipeline"
    governance = root / "governance"
    specialists = root / "specialists"

    mode = "dry-run" if dry_run else "write"
    print(f"agents pull ({mode})  ·  project_id={project_id}  ·  {api_url}")

    errors: list[str] = []
    pulls_ok = True

    def fetch(label: str, endpoint: str) -> Any | None:
        nonlocal pulls_ok
        data, err = _fetch_probe(api_url, endpoint, headers, label)
        if err:
            errors.append(err)
            pulls_ok = False
            print(f"  ✗ {err}")
            return None
        return data

    # Pipeline: tasks
    tasks_ep = f"/api/tasks?project_id={project_id}"
    tasks = fetch("tasks", tasks_ep) or []
    t_path = pipeline / "tasks.json"
    t_body = json.dumps(tasks, indent=2, ensure_ascii=False) + "\n"
    if dry_run:
        print(f"  [dry-run] {t_path}  ←  tasks  (~{_payload_size(tasks)} bytes)")
    else:
        _write(t_path, t_body)

    for key, endpoint, renderer, label in [
        ("blueprints", f"/api/projects/{project_id}/blueprints", render_blueprints, "blueprints"),
        ("session_log", f"/api/projects/{project_id}/session-logs", render_session_log, "session_log"),
        ("execution_trace", f"/api/projects/{project_id}/execution-trace", render_execution_trace, "execution_trace"),
    ]:
        rows = fetch(label, endpoint) or []
        body = renderer(rows)
        out_path = pipeline / f"{key}.md"
        if dry_run:
            print(f"  [dry-run] {out_path}  ←  {label}  (~{len(body.encode('utf-8'))} bytes)")
        else:
            _write(out_path, body)

    for key, endpoint, renderer, label in [
        ("decisions", f"/api/projects/{project_id}/decisions", render_decisions, "decisions"),
        ("memory", f"/api/projects/{project_id}/memory", render_memory, "memory"),
        ("approvals", f"/api/projects/{project_id}/approvals", render_approvals, "approvals"),
        ("backlog", f"/api/projects/{project_id}/backlog", render_backlog, "backlog"),
    ]:
        rows = fetch(label, endpoint) or []
        body = renderer(rows)
        out_path = governance / f"{key}.md"
        if dry_run:
            print(f"  [dry-run] {out_path}  ←  {label}  (~{len(body.encode('utf-8'))} bytes)")
        else:
            _write(out_path, body)

    audit_body = render_audit_trail(None)
    audit_path = governance / "audit_trail.md"
    if dry_run:
        print(f"  [dry-run] {audit_path}  ←  audit_trail (stub)")
    else:
        _write(audit_path, audit_body)

    all_aux = (
        fetch("specialists", f"/api/auxiliary-agent-outputs?project_id={project_id}") or []
    )
    for role in SPECIALIST_ROLES:
        rows = [r for r in all_aux if r.get("agent_role") == role]
        body = render_specialist(role, rows)
        out_path = specialists / f"{role}.md"
        if dry_run:
            print(f"  [dry-run] {out_path}  ←  specialist:{role}  (~{len(body.encode('utf-8'))} bytes)")
        else:
            _write(out_path, body)

    stamp = _now_iso()

    if not dry_run:
        acfg.write_sync_state(
            {
                "last_pull_at": stamp,
                "last_pull_ok": pulls_ok and not errors,
                "pull_errors": errors,
                "api_url": api_url,
                "project_id": project_id,
            },
            cwd=cwd,
        )
    else:
        print("\n(dry-run: no files written, sync_state.json unchanged)")

    if errors and not dry_run:
        print(f"\ncompleted with {len(errors)} error(s); see .claude/sync_state.json")
        return 1
    print("done.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Railway → local .claude/ cache")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and print targets; do not write files or sync_state.json",
    )
    args = parser.parse_args()
    return _sync_impl(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
