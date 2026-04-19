#!/usr/bin/env python3
"""
agents add / agents register  —  POST /api/projects on Railway and persist project_id.

Reads ``.claude/config.json`` for ``api_url`` / ``api_key`` (with ``AGENTS_API_URL`` /
``AGENTS_API_KEY`` fallbacks). Writes back ``project_id`` and ``api_url`` if the URL
came only from the environment.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

try:
    import requests
except ImportError:
    print("error: install requests (pip install requests)", file=sys.stderr)
    sys.exit(1)

import agents_cli_config as acfg


def main() -> int:
    parser = argparse.ArgumentParser(description="Link repo to dashboard API (Railway).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="Register cwd (slug/name optional)")
    p_add.add_argument("slug", nargs="?", default=None)
    p_add.add_argument("name", nargs="?", default=None)

    p_reg = sub.add_parser("register", help="Register explicit slug/name/root_path")
    p_reg.add_argument("slug")
    p_reg.add_argument("name")
    p_reg.add_argument("root_path")

    args = parser.parse_args()

    cwd = Path.cwd()
    cfg_path = acfg.config_path(cwd)
    if not cfg_path.is_file():
        print(f"error: {cfg_path} not found. Run `agents init` in this repo first.", file=sys.stderr)
        return 1

    cfg = acfg.load_config_file(cwd=cwd)
    api_url = acfg.resolve_api_url(cfg, cwd=cwd)
    headers = {"Content-Type": "application/json", **acfg.api_headers(cfg)}

    if args.cmd == "add":
        root = str(cwd.resolve())
        dirname = cwd.name
        slug = (args.slug or dirname.lower().replace(" ", "-")).strip().lower()
        name = (args.name or dirname).strip()
    else:
        root = str(Path(args.root_path).expanduser().resolve())
        slug = str(args.slug).strip().lower()
        name = str(args.name).strip()

    if not slug or not name:
        print("error: slug and name are required", file=sys.stderr)
        return 1

    body = {"name": name, "slug": slug, "root_path": root, "upsert": True}
    url = f"{api_url}/api/projects"
    try:
        r = requests.post(url, headers=headers, json=body, timeout=60)
    except requests.RequestException as e:
        print(f"error: POST {url} failed: {e}", file=sys.stderr)
        return 1

    if r.status_code >= 400:
        print(r.text or r.reason, file=sys.stderr)
        return 1

    try:
        row = r.json()
    except json.JSONDecodeError:
        print("error: response is not JSON", file=sys.stderr)
        return 1

    pid = row.get("id")
    if pid is None:
        print(f"error: response missing id: {row!r}", file=sys.stderr)
        return 1

    try:
        project_id = int(pid)
    except (TypeError, ValueError):
        print(f"error: id is not int: {pid!r}", file=sys.stderr)
        return 1

    updates: dict[str, object] = {"project_id": project_id}
    cfg_url = (cfg.get("api_url") or "").strip()
    if not cfg_url or "REPLACE-WITH-YOUR-RAILWAY" in cfg_url:
        updates["api_url"] = api_url

    acfg.merge_config_updates(updates, cwd=cwd)

    print(json.dumps(row, indent=2, ensure_ascii=False))
    print(f"\nLinked: project_id={project_id}  slug={slug!r}  →  wrote {cfg_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
