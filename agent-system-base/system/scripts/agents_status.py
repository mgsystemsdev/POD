#!/usr/bin/env python3
"""agents status / agents doctor — readiness for Railway API + local DB push."""

from __future__ import annotations

import sys
import time
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

try:
    import requests
except ImportError:
    print("error: pip install requests", file=sys.stderr)
    sys.exit(1)

import agents_cli_config as acfg


def main() -> int:
    cwd = Path.cwd()
    cfg_path = acfg.config_path(cwd)
    print(f"cwd: {cwd}")
    print(f"config: {cfg_path}  ({'exists' if cfg_path.is_file() else 'MISSING'})")

    if not cfg_path.is_file():
        print("\nRun `agents init` then `agents add`.")
        return 1

    cfg = acfg.load_config_file(cwd=cwd)
    api_url = acfg.resolve_api_url(cfg, cwd=cwd)
    key = acfg.resolve_api_key(cfg)
    print(f"api_url: {api_url}")
    print(f"api_key: {'set' if key else 'not set'}")

    pid = cfg.get("project_id")
    print(f"project_id: {pid!r}")

    pg_ok, pg_hint = acfg.database_url_ready()
    print(f"\nDATABASE_URL (push/tasks): {pg_hint}")

    sync = acfg.load_sync_state(cwd=cwd)
    if sync:
        print("\n.claude/sync_state.json:")
        for k in (
            "last_pull_at",
            "last_pull_ok",
            "last_push_at",
            "last_push_ok",
            "pull_errors",
            "last_tasks_import_at",
            "last_tasks_import_ok",
        ):
            if k in sync:
                print(f"  {k}: {sync[k]!r}")

    if pid is None:
        print("\nHTTP probe: skipped (no project_id)")
        return 0

    try:
        project_id = int(pid)
    except (TypeError, ValueError):
        print("\nHTTP probe: skipped (project_id not an integer)")
        return 1

    probe = f"{api_url}/api/projects/{project_id}/blueprints"
    headers = acfg.api_headers(cfg)
    t0 = time.perf_counter()
    try:
        r = requests.get(probe, headers=headers, timeout=20)
        ms = (time.perf_counter() - t0) * 1000
        print(f"\nHTTP GET {probe}")
        print(f"  status: {r.status_code}  ({ms:.0f} ms)")
        if r.status_code >= 400:
            print(f"  body: {r.text[:500]!r}")
            return 1
    except requests.RequestException as e:
        print(f"\nHTTP probe failed: {e}")
        return 1

    print("\nOK: API reachable for this project.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
