#!/usr/bin/env python3
"""
Push per-repo Claude artifacts into the task-dashboard DB and import tasks.

**Note:** Railway Postgres is now the source of truth. Prefer editing via the
dashboard / ChatGPT / API, then `agents pull`. Push is for initial seed /
migration only.

Writes (new 3-folder layout; falls back to legacy flat layout if files are missing):

  - .claude/pipeline/blueprints.md   (legacy: .claude/project.md)       → **Blueprints**
  - .claude/governance/decisions.md  (legacy: .claude/decisions.md)     → **Decisions**
  - .claude/pipeline/session_log.md  (legacy: .claude/session.md)       → **Session Log**
  - .claude/governance/memory.md     (legacy: .claude/memory/MEMORY.md) → **Memory**
  - .claude/governance/backlog.md    → sentinel backlog row (CLI mirror)
  - .claude/specialists/*.md         → ``auxiliary_agent_outputs`` (CLI mirror per role)

Requires ``DATABASE_URL`` to point at Railway Postgres (or local Postgres). Updates
``.claude/sync_state.json`` (``last_push_at``, ``last_tasks_import_*``) on success.

**Global run (same idea as ``task_worker.py``):** with no ``--slug``, reads
``~/agents/agent-services/config/projects_index.json``, processes every **active**
project path, then runs ``workers/task_worker.py`` once with **no extra args**
(global ``~/.claude/tasks.json`` + each active project's tasks).

  cd ~/agents/agent-services && python3 workers/push_claude_artifacts.py

**Single project:** ``--slug dmrb`` (optional ``--root`` if not in the index).

Flags: ``--dry-run``, ``--no-tasks``, ``--global-tasks`` (only with ``--slug``:
also run ``task_worker.py --global-only``).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_SERVICES = Path(__file__).resolve().parent.parent / "services"
_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SERVICES))
sys.path.insert(0, str(_SCRIPTS))

import agents_cli_config as acfg  # noqa: E402
import claude_artifact_sync  # noqa: E402
import project_service  # noqa: E402

PROJECT_MD_TYPE = "project_md"
PROJECT_MD_TITLE = "Project blueprint (.claude/project.md)"

# Same layout as workers/task_worker.py
_SERVICES_ROOT = Path.home() / "agents" / "agent-services"
_PROJECTS_INDEX = _SERVICES_ROOT / "config" / "projects_index.json"


def _resolve_task_worker() -> Path | None:
    home = Path.home()
    candidates = [
        home / "agents" / "agent-services" / "workers" / "task_worker.py",
        Path(__file__).resolve().parents[2] / "workers" / "task_worker.py",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def _load_projects_index() -> list[dict]:
    if not _PROJECTS_INDEX.is_file():
        return []
    try:
        data = json.loads(_PROJECTS_INDEX.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"WARN: could not read {_PROJECTS_INDEX}: {exc}", file=sys.stderr)
        return []
    return list(data.get("projects", []))


def _resolve_targets(slug: str | None, root: Path | None) -> tuple[list[tuple[str, Path]], int]:
    """Return (targets, exit_code). exit_code non-zero means fatal config error."""
    if slug:
        s = slug.strip().lower()
        r = root.resolve() if root is not None else None
        if r is None:
            for p in _load_projects_index():
                if str(p.get("project_id", "")).strip().lower() == s:
                    r = Path(p["project_path"])
                    break
            if r is None:
                print(
                    f"ERROR: slug {slug!r} not in {_PROJECTS_INDEX} — pass --root /path/to/repo",
                    file=sys.stderr,
                )
                return [], 2
        return [(s, r)], 0

    active = [p for p in _load_projects_index() if p.get("status") == "active"]
    out: list[tuple[str, Path]] = []
    for p in active:
        pid = str(p.get("project_id", "")).strip()
        ppath = p.get("project_path")
        if not pid or not ppath:
            continue
        out.append((pid.lower(), Path(ppath)))
    return out, 0


def _sync_markdown_for_project(
    slug: str,
    root: Path,
    *,
    dry_run: bool,
) -> int:
    """Sync project, decisions, session, and ``.claude/memory/MEMORY.md`` into SQLite. Returns 0, or 2 if slug missing."""
    row = project_service.get_project_by_slug(slug)
    if row is None:
        print(
            f"WARN: skip artifact sync for {slug!r} — not in SQLite (POST /api/projects first)",
            file=sys.stderr,
        )
        return 2
    project_id = int(row["id"])
    claude_dir = root / ".claude"

    print(f"=== {slug} ({root}) ===")

    if not root.is_dir():
        print("  [skip] root path does not exist")
        return 0

    if not claude_dir.is_dir():
        print(f"  [skip] no {claude_dir}")
        return 0

    results: list[tuple[str, str, str]] = []

    def _sync_blueprint(path: Path, btype: str, title: str) -> None:
        kind, msg = claude_artifact_sync.upsert_file_blueprint_from_disk(
            project_id,
            path,
            blueprint_type=btype,
            title=title,
            dry_run=dry_run,
        )
        results.append((path.name, kind, msg))

    def _sync_decisions_file(path: Path) -> None:
        kind, msg = claude_artifact_sync.upsert_decisions_file_from_disk(
            project_id, path, dry_run=dry_run
        )
        results.append((path.name + " → decisions", kind, msg))

    def _sync_session_file(path: Path) -> None:
        kind, msg = claude_artifact_sync.upsert_session_file_from_disk(
            project_id, path, dry_run=dry_run
        )
        results.append((path.name + " → session_logs", kind, msg))

    def _first_existing(*candidates: Path) -> Path:
        """Return the first path that exists; else return the first candidate (for error msg)."""
        for p in candidates:
            if p.is_file():
                return p
        return candidates[0]

    # Blueprints: new .claude/pipeline/blueprints.md, fallback to legacy .claude/project.md
    _sync_blueprint(
        _first_existing(claude_dir / "pipeline" / "blueprints.md", claude_dir / "project.md"),
        PROJECT_MD_TYPE,
        PROJECT_MD_TITLE,
    )

    # Decisions: new .claude/governance/decisions.md, fallback to legacy .claude/decisions.md
    _sync_decisions_file(
        _first_existing(claude_dir / "governance" / "decisions.md", claude_dir / "decisions.md")
    )

    # Session Log: new .claude/pipeline/session_log.md, fallback to legacy .claude/session(s).md
    _sync_session_file(
        _first_existing(
            claude_dir / "pipeline" / "session_log.md",
            claude_dir / "sessions.md",
            claude_dir / "session.md",
        )
    )

    # Memory: new .claude/governance/memory.md (single file) or legacy .claude/memory/MEMORY.md folder
    new_memory = claude_dir / "governance" / "memory.md"
    if new_memory.is_file():
        label, kind, msg = claude_artifact_sync.sync_claude_memory_file(
            project_id, new_memory, dry_run=dry_run
        )
        results.append((label, kind, msg))
    else:
        memory_dir = claude_dir / "memory"
        for label, kind, msg in claude_artifact_sync.sync_claude_memory_folder(
            project_id, memory_dir, dry_run=dry_run
        ):
            results.append((label, kind, msg))

    # Backlog (aggregate ``governance/backlog.md`` → sentinel DB row)
    bk_path = claude_dir / "governance" / "backlog.md"
    bk_kind, bk_msg = claude_artifact_sync.sync_backlog_cli_mirror_from_disk(
        project_id, bk_path, dry_run=dry_run
    )
    results.append(("backlog.md → backlog", bk_kind, bk_msg))

    # Specialists (7 files → auxiliary_agent_outputs CLI mirror per role)
    spec_dir = claude_dir / "specialists"
    for role in claude_artifact_sync.SPECIALIST_ROLES_CLI:
        sp = spec_dir / f"{role}.md"
        label, kind, msg = claude_artifact_sync.sync_specialist_file_from_disk(
            project_id, role, sp, dry_run=dry_run
        )
        results.append((label, kind, msg))

    for name, kind, msg in results:
        print(f"  {name}: [{kind}] {msg}")

    if any(k == "error" for _, k, _ in results):
        return 3
    return 0


def _stamp_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _record_push_sync_state(root: Path, *, dry_run: bool, ok: bool) -> None:
    if dry_run:
        return
    try:
        acfg.write_sync_state(
            {
                "last_push_at": _stamp_utc(),
                "last_push_ok": ok,
            },
            cwd=root,
        )
    except OSError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mirror .claude/*.md into dashboard SQLite; then run task import worker "
        "(all active projects by default, like task_worker.py)."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root (single-project mode only; optional if slug is in projects_index.json)",
    )
    parser.add_argument(
        "--slug",
        default=None,
        metavar="ID",
        help="SQLite slug / projects_index project_id — if omitted, all active index entries",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview blueprint writes; do not run import worker",
    )
    parser.add_argument(
        "--no-tasks",
        action="store_true",
        help="Only sync markdown; skip workers/task_worker.py",
    )
    parser.add_argument(
        "--global-tasks",
        action="store_true",
        help="With --slug only: after --project import, also run task_worker.py --global-only",
    )
    args = parser.parse_args()

    if args.global_tasks and not args.slug:
        print("WARN: --global-tasks applies only with --slug; full run already imports ~/.claude/tasks.json", file=sys.stderr)

    targets, resolve_err = _resolve_targets(args.slug, args.root)
    if resolve_err:
        return resolve_err

    if not targets and not args.slug:
        print(f"WARN: no active projects in {_PROJECTS_INDEX}", file=sys.stderr)

    exit_code = 0
    for slug, root in targets:
        rc = _sync_markdown_for_project(slug, root, dry_run=args.dry_run)
        exit_code = max(exit_code, rc)
        if not args.dry_run:
            _record_push_sync_state(root, dry_run=False, ok=(rc == 0))

    if args.no_tasks or args.dry_run:
        if args.dry_run and not args.no_tasks:
            print(
                "(dry-run: would run workers/task_worker.py after artifact sync; "
                "no DB writes from this script besides previews above)"
            )
        return exit_code

    worker = _resolve_task_worker()
    if worker is None:
        print("ERROR: workers/task_worker.py not found", file=sys.stderr)
        return max(exit_code, 3)

    services_root = worker.parent.parent

    task_ok = True
    if args.slug:
        cmd = [sys.executable, str(worker), "--project", args.slug.strip().lower()]
        print("Running:", " ".join(cmd))
        proc = subprocess.run(cmd, cwd=str(services_root))
        exit_code = max(exit_code, int(proc.returncode))
        task_ok = proc.returncode == 0
        if args.global_tasks:
            cmd_g = [sys.executable, str(worker), "--global-only"]
            print("Running:", " ".join(cmd_g))
            proc_g = subprocess.run(cmd_g, cwd=str(services_root))
            exit_code = max(exit_code, int(proc_g.returncode))
            task_ok = task_ok and (proc_g.returncode == 0)
    else:
        cmd = [sys.executable, str(worker)]
        print("Running:", " ".join(cmd))
        proc = subprocess.run(cmd, cwd=str(services_root))
        exit_code = max(exit_code, int(proc.returncode))
        task_ok = proc.returncode == 0

    if not args.dry_run and targets:
        ts = _stamp_utc()
        for _, r in targets:
            acfg.write_sync_state(
                {"last_tasks_import_at": ts, "last_tasks_import_ok": task_ok},
                cwd=r,
            )

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
