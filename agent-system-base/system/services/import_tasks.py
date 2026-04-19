#!/usr/bin/env python3
"""
Import tasks from a JSON array (e.g. ~/.claude/tasks.json) into SQLite via task_service only.

Does not read or write sqlite directly; does not modify the JSON file.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import task_service

_SOURCE_IMPORT = "import"

_PRIORITY_MAP = {1: "low", 2: "normal", 3: "high", 4: "urgent"}


def _map_status(raw: Any) -> str:
    if raw is None:
        return "pending"
    if str(raw).lower() == "complete":
        return "done"
    return "pending"


def _map_priority(raw: Any) -> str:
    if raw is None:
        return "normal"
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return "normal"
    return _PRIORITY_MAP.get(n, "normal")


def _dedupe_key(source: str, title: str, created_norm: str) -> tuple[str, str, str]:
    return (source, title, created_norm)


def main(argv: list[str] | None = None) -> int:
    print("Do NOT run while worker is active")

    default_json = Path.home() / ".claude" / "tasks.json"
    parser = argparse.ArgumentParser(description="Import tasks.json into SQLite (task_service only).")
    parser.add_argument("--project-id", type=int, required=True, help="Target project id.")
    parser.add_argument(
        "--tasks-json",
        type=Path,
        default=default_json,
        help=f"Path to JSON array (default: {default_json})",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned inserts only; no DB writes.")
    args = parser.parse_args(argv)

    if not task_service.project_exists(args.project_id):
        print(
            f"Error: project_id {args.project_id} not found in projects table (foreign key would fail on insert).",
            file=sys.stderr,
        )
        print("Create a project first, then pass its id.", file=sys.stderr)
        return 1

    path = args.tasks_json.expanduser()
    if not path.is_file():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON: {e}", file=sys.stderr)
        return 1

    if not isinstance(raw, list):
        print("Error: JSON root must be a list", file=sys.stderr)
        return 1

    existing = task_service.list_tasks(project_id=args.project_id)
    seen: set[tuple[str, str, str]] = set()
    for t in existing:
        try:
            cn = task_service.normalize_timestamp(str(t["created_at"]))
        except (TypeError, ValueError):
            cn = str(t["created_at"])
        seen.add(_dedupe_key(str(t["source"]), str(t["title"]), cn))

    inserted = 0
    skipped = 0
    errors = 0

    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            print(f"Skip row {idx}: not an object", file=sys.stderr)
            errors += 1
            continue

        title = item.get("title")
        if not title or not isinstance(title, str):
            print(f"Skip row {idx}: missing title", file=sys.stderr)
            errors += 1
            continue

        created_raw = item.get("created_at")
        if not created_raw or not isinstance(created_raw, str):
            print(f"Skip row {idx}: missing created_at", file=sys.stderr)
            errors += 1
            continue

        try:
            created_norm = task_service.normalize_timestamp(created_raw)
        except (TypeError, ValueError) as e:
            print(f"Skip row {idx}: bad created_at: {e}", file=sys.stderr)
            errors += 1
            continue

        updated_raw = item.get("updated_at")
        if isinstance(updated_raw, str) and updated_raw.strip():
            try:
                updated_norm = task_service.normalize_timestamp(updated_raw)
            except (TypeError, ValueError) as e:
                print(f"Skip row {idx}: bad updated_at: {e}", file=sys.stderr)
                errors += 1
                continue
        else:
            updated_norm = created_norm

        key = _dedupe_key(_SOURCE_IMPORT, title, created_norm)
        if key in seen:
            skipped += 1
            continue

        status = _map_status(item.get("status"))
        priority = _map_priority(item.get("priority"))
        description = item.get("description")
        if description is not None and not isinstance(description, str):
            description = str(description)

        if args.dry_run:
            print(f"WOULD INSERT: {title!r}")
        else:
            task_service.create_task(
                args.project_id,
                title,
                description=description,
                status=status,
                priority=priority,
                task_type="chore",
                source=_SOURCE_IMPORT,
                created_at=created_norm,
                updated_at=updated_norm,
            )

        seen.add(key)
        inserted += 1

    if args.dry_run:
        print(f"Summary: would_insert={inserted} skipped={skipped} errors={errors}")
    else:
        print(f"Summary: inserted={inserted} skipped={skipped} errors={errors}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
