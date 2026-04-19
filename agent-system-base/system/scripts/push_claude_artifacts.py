#!/usr/bin/env python3
"""
Push per-repo Claude artifacts into the task-dashboard SQLite DB and import tasks.

Writes:

  - .claude/project.md → ``blueprints`` (``project_md``) — **Blueprints** tab
  - .claude/decisions.md → ``decisions`` (file-mirror upsert) — **Decisions** tab
  - .claude/sessions.md or .claude/session.md → ``session_logs`` (file-mirror upsert) — **Session Log** tab
  - .claude/memory/MEMORY.md → ``memory`` key ``mirror/memory/MEMORY.md`` — **Memory** tab

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
from pathlib import Path

_SERVICES = Path(__file__).resolve().parent.parent / "services"
sys.path.insert(0, str(_SERVICES))

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

    _sync_blueprint(claude_dir / "project.md", PROJECT_MD_TYPE, PROJECT_MD_TITLE)
    _sync_decisions_file(claude_dir / "decisions.md")

    session_file = claude_dir / "sessions.md"
    if not session_file.is_file():
        session_file = claude_dir / "session.md"
    _sync_session_file(session_file)

    memory_dir = claude_dir / "memory"
    for label, kind, msg in claude_artifact_sync.sync_claude_memory_folder(
        project_id, memory_dir, dry_run=dry_run
    ):
        results.append((label, kind, msg))

    for name, kind, msg in results:
        print(f"  {name}: [{kind}] {msg}")
    return 0


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

    if args.no_tasks or args.dry_run:
        if args.dry_run and not args.no_tasks:
            print("(dry-run: skipping task_worker.py)")
        return exit_code

    worker = _resolve_task_worker()
    if worker is None:
        print("ERROR: workers/task_worker.py not found", file=sys.stderr)
        return max(exit_code, 3)

    services_root = worker.parent.parent

    if args.slug:
        cmd = [sys.executable, str(worker), "--project", args.slug.strip().lower()]
        print("Running:", " ".join(cmd))
        proc = subprocess.run(cmd, cwd=str(services_root))
        exit_code = max(exit_code, int(proc.returncode))
        if args.global_tasks:
            cmd_g = [sys.executable, str(worker), "--global-only"]
            print("Running:", " ".join(cmd_g))
            proc_g = subprocess.run(cmd_g, cwd=str(services_root))
            exit_code = max(exit_code, int(proc_g.returncode))
    else:
        cmd = [sys.executable, str(worker)]
        print("Running:", " ".join(cmd))
        proc = subprocess.run(cmd, cwd=str(services_root))
        exit_code = max(exit_code, int(proc.returncode))

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
