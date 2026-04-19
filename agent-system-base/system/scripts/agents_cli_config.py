"""
Shared config for Railway-first ``agents`` CLI scripts (pull, link, status).

Resolves ``api_url`` and ``api_key`` from ``.claude/config.json`` with
``AGENTS_API_URL`` / ``AGENTS_API_KEY`` env fallbacks.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

CONFIG_REL = Path(".claude/config.json")
SYNC_STATE_REL = Path(".claude/sync_state.json")


def config_path(cwd: Path | None = None) -> Path:
    base = cwd or Path.cwd()
    return base / CONFIG_REL


def sync_state_path(cwd: Path | None = None) -> Path:
    base = cwd or Path.cwd()
    return base / SYNC_STATE_REL


def load_claude_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        print(f"error: {path} not found. Run `agents init` first.", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"error: {path} is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)


def load_config_file(*, cwd: Path | None = None) -> dict[str, Any]:
    return load_claude_json(config_path(cwd))


def resolve_api_url(cfg: dict[str, Any], *, cwd: Path | None = None) -> str:
    raw = (cfg.get("api_url") or "").strip().rstrip("/")
    if not raw or "REPLACE-WITH-YOUR-RAILWAY" in raw:
        raw = (os.environ.get("AGENTS_API_URL") or "").strip().rstrip("/")
    url = raw
    if not url:
        print(
            "error: api_url missing. Set it in .claude/config.json or export AGENTS_API_URL "
            "(e.g. https://your-app.up.railway.app).",
            file=sys.stderr,
        )
        sys.exit(1)
    return url


def resolve_api_key(cfg: dict[str, Any]) -> str | None:
    key = cfg.get("api_key")
    if key is not None and str(key).strip():
        return str(key).strip()
    env_k = os.environ.get("AGENTS_API_KEY")
    if env_k and env_k.strip():
        return env_k.strip()
    return None


def api_headers(cfg: dict[str, Any]) -> dict[str, str]:
    h: dict[str, str] = {}
    key = resolve_api_key(cfg)
    if key:
        h["X-API-Key"] = key
    return h


def require_project_id(cfg: dict[str, Any]) -> int:
    pid = cfg.get("project_id")
    if pid is None:
        print(
            "error: project_id missing in .claude/config.json. Run `agents add` first.",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        return int(pid)
    except (TypeError, ValueError):
        print(f"error: project_id must be an integer, got {pid!r}", file=sys.stderr)
        sys.exit(1)


def save_config(cfg: dict[str, Any], *, cwd: Path | None = None) -> None:
    path = config_path(cwd)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def merge_config_updates(
    updates: dict[str, Any],
    *,
    cwd: Path | None = None,
) -> dict[str, Any]:
    """Load config, apply ``updates``, write. Returns merged dict."""
    path = config_path(cwd)
    if not path.is_file():
        cfg: dict[str, Any] = {}
    else:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    cfg.update(updates)
    save_config(cfg, cwd=cwd)
    return cfg


def load_sync_state(*, cwd: Path | None = None) -> dict[str, Any]:
    p = sync_state_path(cwd)
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_sync_state(updates: dict[str, Any], *, cwd: Path | None = None) -> None:
    """Merge ``updates`` into ``.claude/sync_state.json``."""
    p = sync_state_path(cwd)
    cur = load_sync_state(cwd=cwd)
    cur.update(updates)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cur, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def database_url_ready() -> tuple[bool, str]:
    """Return (is_postgres_ready, hint_message)."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        return False, "DATABASE_URL not set (required for agents push / agents tasks → Railway Postgres)."
    if url.startswith(("postgres://", "postgresql://")):
        return True, "DATABASE_URL points at Postgres."
    return False, f"DATABASE_URL is set but not a postgres URL (starts with {url[:12]!r}...)."


def is_postgres_database_url() -> bool:
    url = os.environ.get("DATABASE_URL", "")
    return url.startswith(("postgres://", "postgresql://"))
