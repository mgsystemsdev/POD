#!/usr/bin/env python3
"""
Read-only system integrity audit (T08).

Scans configured roots for forbidden live-state files, detects JSON/SQLite overlap,
validates crontab worker lines, and flags architecture violations in system/services.

Allowlists (env, colon-separated paths relative to each scan root, forward slashes):
  AUDIT_ALLOWLIST — applies to tasks.json, decisions.csv, and memory/**/*.md matches
  AUDIT_PROJECT_ROOTS — extra roots to scan (default: repository root only)
  AUDIT_NO_DEFAULT_ROOT — if set, do not scan the repository root (tests / custom roots only)

Default allowlist (merged with AUDIT_ALLOWLIST / --allowlist):
  - .claude/memory  (cross-project memory during JSON→SQLite migration)

Does not write files or open network connections.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# system/scripts/audit.py -> parents[2] = repository root (agent-system-base)
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SERVICES_DIR = _REPO_ROOT / "system" / "services"

if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

import task_service  # noqa: E402

_SKIP_DIR_NAMES = frozenset(
    {".git", "__pycache__", ".venv", "venv", "node_modules", ".tox", ".mypy_cache", "dist", "build"}
)

# Default paths allowlisted under each scan root (migration / known safe trees)
_DEFAULT_ALLOWLIST: frozenset[str] = frozenset({".claude/memory"})


def _parse_extra_roots(arg: str | None) -> list[Path]:
    if not arg:
        return []
    return [Path(p.strip()).expanduser().resolve() for p in arg.split(":") if p.strip()]


def _parse_env_roots() -> list[Path]:
    env = os.environ.get("AUDIT_PROJECT_ROOTS", "").strip()
    if not env:
        return []
    return [Path(p.strip()).expanduser().resolve() for p in env.split(":") if p.strip()]


def _parse_allowlist(env_val: str | None, cli: list[str]) -> set[str]:
    out: set[str] = set(_DEFAULT_ALLOWLIST)
    if env_val:
        for p in env_val.split(":"):
            p = p.strip().replace("\\", "/")
            if p:
                out.add(p)
    for p in cli:
        out.add(p.replace("\\", "/"))
    return out


def _rel_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _is_under_allowlist(rel: str, allow: set[str]) -> bool:
    if rel in allow:
        return True
    for prefix in allow:
        if prefix.endswith("/") and rel.startswith(prefix.rstrip("/")):
            return True
        if rel == prefix or rel.startswith(prefix + "/"):
            return True
    return False


def check_illegal_files(roots: list[Path], allow: set[str]) -> tuple[list[str], list[Path]]:
    violations: list[str] = []
    illegal_tasks_json: list[Path] = []

    for root in roots:
        if not root.is_dir():
            violations.append(f"illegal-files: scan root is not a directory: {root}")
            continue
        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIR_NAMES]
            pdir = Path(dirpath)
            for name in filenames:
                full = pdir / name
                try:
                    rel = _rel_posix(full, root)
                except ValueError:
                    continue
                if _is_under_allowlist(rel, allow):
                    continue

                if name == "tasks.json":
                    violations.append(f"tasks.json (not allowlisted): {full}")
                    illegal_tasks_json.append(full)
                elif name == "decisions.csv":
                    violations.append(f"decisions.csv (not allowlisted): {full}")

            for name in filenames:
                if not name.endswith(".md"):
                    continue
                full = pdir / name
                if "memory" not in full.parts:
                    continue
                try:
                    rel = _rel_posix(full, root)
                except ValueError:
                    continue
                if _is_under_allowlist(rel, allow):
                    continue
                violations.append(f"memory/**/*.md (live state risk): {full}")

    return violations, illegal_tasks_json


def _task_key(source: str, title: str, created_at: str) -> tuple[str, str, str]:
    ts = task_service.normalize_timestamp(created_at)
    return (source, title, ts)


def check_multiple_sources(illegal_json_paths: list[Path]) -> list[str]:
    violations: list[str] = []
    if not illegal_json_paths:
        print("INFO: No unallowlisted tasks.json found; skipping SQLite overlap check.")
        return violations

    sqlite_tasks = task_service.list_tasks()
    sqlite_keys: set[tuple[str, str, str]] = set()
    for t in sqlite_tasks:
        try:
            sqlite_keys.add(
                _task_key(str(t["source"]), str(t["title"]), str(t["created_at"]))
            )
        except (TypeError, ValueError) as e:
            violations.append(f"overlap-check: could not normalize SQLite task id={t.get('id')}: {e}")

    for path in illegal_json_paths:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            violations.append(f"overlap-check: cannot read JSON {path}: {e}")
            continue
        if not isinstance(raw, list):
            violations.append(f"overlap-check: {path} root is not a list")
            continue
        for i, item in enumerate(raw):
            if not isinstance(item, dict):
                continue
            title = item.get("title")
            created = item.get("created_at")
            if not title or not isinstance(title, str) or not created or not isinstance(created, str):
                continue
            src = item.get("source")
            source = str(src) if isinstance(src, str) and src else "manual"
            try:
                key = _task_key(source, title, created)
            except (TypeError, ValueError):
                continue
            if key in sqlite_keys:
                violations.append(
                    f"overlap: JSON entry matches SQLite (source,title,created_at) — {path} index={i} title={title!r}"
                )
    return violations


def check_crontab() -> list[str]:
    violations: list[str] = []
    try:
        r = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as e:
        print(f"INFO: crontab not available: {e}")
        return violations

    if r.returncode != 0:
        print("INFO: No user crontab (or crontab -l failed); skipping worker line validation.")
        return violations

    lines = [ln for ln in r.stdout.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    worker_lines = [ln for ln in lines if "task_worker" in ln]

    if not worker_lines:
        print("INFO: No cron lines referencing task_worker; nothing to validate.")
        return violations

    seen: set[str] = set()
    for ln in worker_lines:
        if ln in seen:
            violations.append(f"cron: duplicate worker line: {ln.strip()}")
        seen.add(ln)
        if "source" not in ln or ".env" not in ln:
            violations.append(f"cron: worker line must source .env: {ln.strip()}")
        if "task_worker" in ln and "agent-services" not in ln and "agent-system-base" not in ln:
            violations.append(
                f"cron: worker line should reference agent-services or agent-system-base path: {ln.strip()}"
            )

    if len(worker_lines) > 1:
        violations.append(
            f"cron: multiple task_worker cron entries ({len(worker_lines)}); expected a single worker line"
        )

    return violations


def _line_suggests_open_write(line: str) -> bool:
    if "open(" not in line:
        return False
    if re.search(r"""['"]w['"]""", line):
        return True
    if re.search(r"""mode\s*=\s*["']w["']""", line):
        return True
    return False


def check_services_architecture() -> list[str]:
    violations: list[str] = []
    if not _SERVICES_DIR.is_dir():
        return [f"architecture: system/services not found: {_SERVICES_DIR}"]

    for path in sorted(_SERVICES_DIR.glob("**/*.py")):
        if path.name == "db.py":
            continue
        if path.name.startswith("test_"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            violations.append(f"architecture: cannot read {path}: {e}")
            continue
        rel = path.relative_to(_REPO_ROOT).as_posix()
        for i, line in enumerate(text.splitlines(), 1):
            if "import sqlite3" in line:
                violations.append(f"architecture: import sqlite3 — {rel}:{i}: {line.strip()}")
            if _line_suggests_open_write(line):
                violations.append(f"architecture: open write — {rel}:{i}: {line.strip()}")

    return violations


def run_audit(roots: list[Path], allow: set[str]) -> int:
    all_v: list[str] = []

    print("=== CHECK 1: Illegal files ===")
    v1, illegal_json = check_illegal_files(roots, allow)
    if v1:
        for x in v1:
            print(f"- {x}")
            all_v.append(x)
    else:
        print("- (none)")
    print()

    print("=== CHECK 2: Multiple data sources (JSON vs SQLite) ===")
    v2 = check_multiple_sources(illegal_json)
    if v2:
        for x in v2:
            print(f"- {x}")
        all_v.extend(v2)
    else:
        if illegal_json:
            print("- (none)")
        else:
            print("- (skipped — no illegal tasks.json)")
    print()

    print("=== CHECK 3: Worker misconfiguration (crontab) ===")
    v3 = check_crontab()
    if v3:
        for x in v3:
            print(f"- {x}")
        all_v.extend(v3)
    else:
        print("- (none)")
    print()

    print("=== CHECK 4: Broken architecture (system/services) ===")
    v4 = check_services_architecture()
    if v4:
        for x in v4:
            print(f"- {x}")
        all_v.extend(v4)
    else:
        print("- (none)")
    print()

    if all_v:
        print("AUDIT: FAIL")
        return 1
    print("AUDIT: OK")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only system integrity audit.")
    parser.add_argument(
        "--roots",
        default=None,
        help="Extra scan roots (colon-separated); merged with AUDIT_PROJECT_ROOTS and default repo root.",
    )
    parser.add_argument(
        "--allowlist",
        action="append",
        default=[],
        metavar="REL_PATH",
        help="Relative path (from each root) allowlisted for tasks.json, decisions.csv, memory/**/*.md.",
    )
    args = parser.parse_args(argv)

    roots: list[Path] = []
    if not os.environ.get("AUDIT_NO_DEFAULT_ROOT"):
        roots.append(_REPO_ROOT)
    roots.extend(_parse_extra_roots(args.roots))
    roots.extend(_parse_env_roots())

    if not roots:
        print("Error: no scan roots (set AUDIT_NO_DEFAULT_ROOT=0 or pass --roots / AUDIT_PROJECT_ROOTS)")
        return 2

    seen: set[Path] = set()
    uniq: list[Path] = []
    for r in roots:
        r = r.resolve()
        if r not in seen:
            seen.add(r)
            uniq.append(r)
    roots = uniq

    allow = _parse_allowlist(os.environ.get("AUDIT_ALLOWLIST"), args.allowlist)

    return run_audit(roots, allow)


if __name__ == "__main__":
    sys.exit(main())
