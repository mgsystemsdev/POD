#!/usr/bin/env python3
"""
T12.2–T12.4: Load project markdown, parse candidates, dedupe + insert via ``task_service``.

Preview by default; use ``--apply`` for idempotent inserts (``source=project_import``).
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, NamedTuple

import context_loader
import project_service
import task_service

_SOURCE_PROJECT_IMPORT = "project_import"

# Only these basenames under project root_path (T12.2 scope).
MARKDOWN_FILES: tuple[str, ...] = ("AGENTS.md", "WORKFLOW.md", "TASKS.md")

_TASKS_FILENAME = "TASKS.md"
_HEADING_FILES = frozenset({"AGENTS.md", "WORKFLOW.md"})
# ## or ### at line start
_HEADING_RE = re.compile(r"^#{2,3}\s+(.+)$")
# Deterministic timestamps: fixed UTC epoch + monotonic index (no wall clock).
_INGEST_BASE_UTC = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def _deterministic_ts(global_index: int) -> str:
    dt = _INGEST_BASE_UTC + timedelta(seconds=global_index)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_heading_sections(content: str) -> list[tuple[str, str | None]]:
    """Each ``##`` / ``###`` heading → (title, description until next heading)."""
    lines = content.splitlines()
    results: list[tuple[str, str | None]] = []
    i = 0
    while i < len(lines):
        m = _HEADING_RE.match(lines[i])
        if not m:
            i += 1
            continue
        title = m.group(1).strip()
        i += 1
        desc_lines: list[str] = []
        while i < len(lines):
            if _HEADING_RE.match(lines[i]):
                break
            desc_lines.append(lines[i])
            i += 1
        body = "\n".join(desc_lines).strip()
        results.append((title, body if body else None))
    return results


def _parse_tasks_bullets(content: str) -> list[str]:
    """``- `` / ``* `` lines → title text (description empty at ingest)."""
    out: list[str] = []
    for line in content.splitlines():
        s = line.lstrip()
        if s.startswith("- ") or s.startswith("* "):
            title = s[2:].strip()
            if title:
                out.append(title)
    return out


def parse_tasks(file_map: dict[str, str]) -> list[dict[str, Any]]:
    """
    Extract task-shaped dicts from markdown (no I/O, no DB).

    Files are processed in **sorted filename order** (``AGENTS.md``, ``TASKS.md``, ``WORKFLOW.md``).
    ``created_at`` / ``updated_at`` are deterministic (ingest epoch + monotonic second index).
    Same ``file_map`` → identical list.
    """
    rows: list[dict[str, Any]] = []
    idx = 0
    for fname in sorted(file_map.keys()):
        content = file_map[fname]
        if fname == _TASKS_FILENAME:
            for title in _parse_tasks_bullets(content):
                ts = _deterministic_ts(idx)
                idx += 1
                rows.append(
                    {
                        "title": title,
                        "description": None,
                        "priority": "normal",
                        "type": "feature",
                        "created_at": ts,
                        "updated_at": ts,
                    }
                )
        elif fname in _HEADING_FILES:
            for title, desc in _parse_heading_sections(content):
                if not title.strip():
                    continue
                ts = _deterministic_ts(idx)
                idx += 1
                rows.append(
                    {
                        "title": title.strip(),
                        "description": desc,
                        "priority": "normal",
                        "type": "feature",
                        "created_at": ts,
                        "updated_at": ts,
                    }
                )
    return rows


class IngestSummary(NamedTuple):
    """Preview: ``inserted`` is always 0. Apply: ``would_insert`` is always 0."""

    would_insert: int
    inserted: int
    skipped: int


def _dedupe_key(source: str, title: str, created_norm: str) -> tuple[str, str, str]:
    return (source, title, created_norm)


def _existing_keys(project_id: int) -> set[tuple[str, str, str]]:
    """Keys matching ``import_tasks`` / ``task_service.normalize_timestamp``."""
    seen: set[tuple[str, str, str]] = set()
    for t in task_service.list_tasks(project_id=project_id):
        try:
            cn = task_service.normalize_timestamp(str(t["created_at"]))
        except (TypeError, ValueError):
            cn = str(t["created_at"])
        seen.add(_dedupe_key(str(t["source"]), str(t["title"]), cn))
    return seen


def ingest_parsed_tasks(
    project_id: int,
    candidates: list[dict[str, Any]],
    *,
    apply: bool,
) -> IngestSummary:
    """
    Dedupe on ``(source, title, created_at)`` with normalized timestamps.

    If ``apply`` is False: print ``WOULD INSERT`` only; **no DB writes**. Counts go to
    ``would_insert``; ``inserted`` is always 0.

    If ``apply`` is True: call ``task_service.create_task``; counts go to ``inserted``;
    ``would_insert`` is always 0.
    """
    seen = _existing_keys(project_id)
    would_insert = 0
    inserted = 0
    skipped = 0

    for c in candidates:
        try:
            cn = task_service.normalize_timestamp(str(c["created_at"]))
        except (TypeError, ValueError):
            print(f"Skip candidate (bad created_at): {c!r}", file=sys.stderr)
            skipped += 1
            continue

        key = _dedupe_key(_SOURCE_PROJECT_IMPORT, str(c["title"]), cn)
        if key in seen:
            skipped += 1
            continue

        if not apply:
            print(f"WOULD INSERT: {c['title']!r}")
            would_insert += 1
            seen.add(key)
            continue

        task_service.create_task(
            project_id,
            str(c["title"]),
            description=c.get("description"),
            status="pending",
            priority=str(c["priority"]),
            task_type=str(c["type"]),
            source=_SOURCE_PROJECT_IMPORT,
            created_at=str(c["created_at"]),
            updated_at=str(c["updated_at"]),
        )
        inserted += 1
        seen.add(key)

    if apply:
        assert would_insert == 0, "preview counter must stay 0 when apply=True"
    else:
        assert inserted == 0, "inserted must stay 0 in preview (dry-run); use would_insert"

    return IngestSummary(would_insert=would_insert, inserted=inserted, skipped=skipped)


def _print_ingest_summary(apply: bool, summary: IngestSummary) -> None:
    """Print summary lines; never label preview counts as ``inserted``."""
    print("Ingest summary:")
    if apply:
        print(f"  inserted: {summary.inserted}")
        print(f"  would_insert: {summary.would_insert}")
    else:
        print(f"  would_insert: {summary.would_insert}")
        print(f"  inserted: {summary.inserted}")
    print(f"  skipped: {summary.skipped}")


def read_project_markdown_files(root: Path) -> tuple[dict[str, str], list[str]]:
    """
    Read known markdown files under ``root`` (UTF-8).

    Returns ``(contents_by_filename, issues)`` where ``issues`` lists missing paths
    or files that could not be read (still graceful — no exception for missing).
    """
    contents: dict[str, str] = {}
    issues: list[str] = []
    for name in MARKDOWN_FILES:
        path = root / name
        if not path.is_file():
            issues.append(f"missing: {name}")
            continue
        try:
            contents[name] = path.read_text(encoding="utf-8")
        except OSError as e:
            issues.append(f"unreadable: {name} ({e})")
    return contents, issues


def run_loader(
    *,
    project_id: int | None,
    slug: str | None,
    apply: bool,
) -> int:
    """Resolve project, load markdown, parse, dedupe/insert. Returns process exit code."""
    if (project_id is None) == (slug is None):
        print("Error: exactly one of --project-id or --slug is required.", file=sys.stderr)
        return 2

    if project_id is not None:
        project = project_service.get_project(project_id)
    else:
        assert slug is not None
        project = project_service.get_project_by_slug(slug)

    if project is None:
        ident = f"id={project_id}" if project_id is not None else f"slug={slug!r}"
        print(f"Error: project not found ({ident}).", file=sys.stderr)
        return 1

    try:
        ctx = context_loader.load_project_context(project_id=project_id, slug=slug)
    except (LookupError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    project = ctx["project"]
    root = ctx["root"]
    root_exists = ctx["root_exists"]

    raw_root = project.get("root_path")
    if not raw_root or not str(raw_root).strip():
        print("Error: project has no root_path set; cannot load markdown.", file=sys.stderr)
        return 1

    if root is None or not root_exists:
        print(
            f"Error: root_path is not a valid directory: {raw_root!r}",
            file=sys.stderr,
        )
        return 1

    contents, issues = read_project_markdown_files(root)

    total_chars = sum(len(s) for s in contents.values())
    total_lines = sum(s.count("\n") + (1 if s else 0) for s in contents.values())

    mode = "apply" if apply else "dry-run (no DB writes)"
    print(f"ingest_project_tasks ({mode})")
    print()
    print(f"Project: {project['name']} ({project['slug']})")
    print(f"Root:    {root}")
    print()
    print("Files:")
    for name in MARKDOWN_FILES:
        state = "read" if name in contents else "missing"
        print(f"  - {name}  ({state})")
    for line in issues:
        print(f"  note: {line}")
    print()
    print("Summary:")
    print(f"  files found: {len(contents)} / {len(MARKDOWN_FILES)}")
    print(f"  total chars: {total_chars}")
    print(f"  total lines: {total_lines}")
    candidates = parse_tasks(contents)
    print()
    print(f"Parsed task candidates: {len(candidates)}")

    pid = int(project["id"])
    summary = ingest_parsed_tasks(pid, candidates, apply=apply)
    print()
    _print_ingest_summary(apply, summary)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ingest project markdown into tasks (preview by default; --apply to insert).",
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--project-id", type=int, metavar="ID", help="SQLite projects.id")
    g.add_argument("--slug", type=str, metavar="SLUG", help="Project slug")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Insert tasks (source=project_import). Default is preview (WOULD INSERT, no writes).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Optional; preview is already the default (kept for script compatibility).",
    )
    args = parser.parse_args(argv)
    # Preview must win over --apply so dry-run never writes or mis-labels counts.
    apply = bool(args.apply) and not bool(args.dry_run)

    return run_loader(
        project_id=args.project_id,
        slug=args.slug,
        apply=apply,
    )


if __name__ == "__main__":
    sys.exit(main())
