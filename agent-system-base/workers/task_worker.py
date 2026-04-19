#!/usr/bin/env python3
"""
Global Task Worker — imports tasks from tasks.json into SQLite (single source of truth).

SQLite is the execution queue. This worker bridges tasks.json → SQLite only.
The SQLite worker (system/services/task_worker.py) handles actual execution.

Behaviour by action_type:
  log_only          — executed inline here (no AI, no import needed)
  ingest_blueprint  — writes blueprint row for resolved SQLite project
  ingest_decision   — append decision row for resolved SQLite project
  ingest_memory     — upsert memory row for resolved SQLite project
  ingest_session_log — append session_logs row for resolved SQLite project
  claude_execute    — imported to SQLite as a pending task; SQLite worker executes
  run_script        — imported to SQLite as a pending task; SQLite worker executes
  generate_file     — imported to SQLite as a pending task; SQLite worker executes
  run_plan          — imported to SQLite as a pending task; SQLite worker executes

Sources:
  1. ~/.claude/tasks.json              — global task board (imports to SQLite ``claude-global`` by default)
  2. Per-project tasks.json            — from each project in projects_index.json

After each active project run, ``.claude/project.md`` (when present) is upserted into SQLite
blueprints (type ``project_md``) so the dashboard Blueprint tab matches the file.

Optional per-task fields (tasks.json):
  - sqlite_project_slug (alias project_slug) — force SQLite project; slug must exist in the DB.
    Use when the row is in ~/.claude/tasks.json but work belongs to e.g. dmrb (not Global Claude).
  - execution_mode: "manual" or prefer_manual: true — imported description notes to use
    task_worker.py --mode manual (no Anthropic API).

State:  ~/agents/agent-services/state/task_worker_state.json
Logs:   ~/agents/agent-services/logs/task_worker.log

Usage:
    python task_worker.py                     # all sources
    python task_worker.py --dry-run           # preview, no writes
    python task_worker.py --project dmrb      # single project only
    python task_worker.py --global-only       # only ~/.claude/tasks.json
"""

import json
import argparse
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

SERVICES_ROOT  = Path.home() / "agents" / "agent-services"
CONFIG_DIR     = SERVICES_ROOT / "config"
PROJECTS_INDEX = CONFIG_DIR / "projects_index.json"
LOG_FILE       = SERVICES_ROOT / "logs" / "task_worker.log"
STATE_FILE     = SERVICES_ROOT / "state" / "task_worker_state.json"
GLOBAL_TASKS   = Path.home() / ".claude" / "tasks.json"

REQUIRED_ENV_KEYS = ["ANTHROPIC_API_KEY"]

# ── SQLite service layer ───────────────────────────────────────────────────────
# Optional: if services dir is present, task imports go to SQLite.
# If absent (e.g. in testing), log_only tasks still work; others are blocked.

_SERVICES_DIR = Path.home() / "agents" / "agent-system-base" / "system" / "services"
_SQLITE_AVAILABLE = False
if _SERVICES_DIR.is_dir():
    sys.path.insert(0, str(_SERVICES_DIR))
    _SQLITE_AVAILABLE = True

# ── Logging ───────────────────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(
    source: str,
    level: str,
    message: str,
    *,
    task_id: str = "",
    action_type: str = "",
    result: str = "",
    dry_run: bool = False,
) -> None:
    entry = {
        "ts": now_iso(),
        "level": level,
        "source": source,
        "message": ("[DRY-RUN] " if dry_run else "") + message,
    }
    if task_id:
        entry["task_id"] = task_id
    if action_type:
        entry["action_type"] = action_type
    if result:
        entry["result"] = result

    line = json.dumps(entry)
    print(line)
    if not dry_run:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a") as f:
            f.write(line + "\n")


# ── SQLite import helper ──────────────────────────────────────────────────────

_PRIORITY_MAP = {1: "urgent", 2: "high", 3: "normal", 4: "low", 5: "low"}

# Dashboard Blueprint tab reads SQLite `blueprints`; mirror disk project.md there.
_PROJECT_MD_BLUEPRINT_TYPE = "project_md"
_PROJECT_MD_BLUEPRINT_TITLE = "Project blueprint (.claude/project.md)"


def sync_project_md_blueprint(
    project_path: Path,
    project_id: int | None,
    dry_run: bool,
) -> tuple[str, str]:
    """
    Upsert ``.claude/project.md`` into blueprint rows so the dashboard shows it.

    Returns (kind, message) for logging; kind is skipped|unchanged|updated|created|error|dry-run.
    """
    if project_id is None:
        return "skipped", "no SQLite project_id"
    if not _SQLITE_AVAILABLE:
        return "skipped", "SQLite unavailable"
    import claude_artifact_sync  # noqa: PLC0415

    pm = project_path / ".claude" / "project.md"
    return claude_artifact_sync.upsert_file_blueprint_from_disk(
        project_id,
        pm,
        blueprint_type=_PROJECT_MD_BLUEPRINT_TYPE,
        title=_PROJECT_MD_BLUEPRINT_TITLE,
        dry_run=dry_run,
    )


def _sqlite_project_id_for(source: str, projects_index_entry: dict | None) -> int | None:
    """
    Resolve the SQLite project id for a tasks.json source.

    - For the global queue ("global"), returns the id of the 'claude-global' project.
    - For per-project sources, tries to match by slug from the projects_index entry.
    - Returns None if services unavailable or project not found (caller falls back to project 1).
    """
    if not _SQLITE_AVAILABLE:
        return None
    try:
        import project_service  # noqa: PLC0415
        if source == "global":
            row = project_service.get_project_by_slug("claude-global")
        elif projects_index_entry:
            slug = projects_index_entry.get("project_id", "")
            row = project_service.get_project_by_slug(slug)
            if row is None:
                row = project_service.get_project_by_slug("claude-global")
        else:
            row = project_service.get_project_by_slug("claude-global")
        return int(row["id"]) if row else None
    except Exception:
        return None


def _final_sqlite_project_id(
    task: dict,
    *,
    sqlite_project_id: int | None,
    source: str,
    projects_index_entry: dict | None,
) -> tuple[int | None, str | None]:
    """
    Choose SQLite project_id for import.

    If the task sets sqlite_project_slug (alias project_slug), that slug wins and must
    exist in the DB — avoids silently landing work in Global Claude when it belongs elsewhere.

    Returns (project_id, None) or (None, error_message) when slug is set but invalid.
    """
    slug = (task.get("sqlite_project_slug") or task.get("project_slug") or "").strip()
    if slug:
        if not _SQLITE_AVAILABLE:
            return None, "SQLite services unavailable — cannot resolve sqlite_project_slug"
        try:
            import project_service  # noqa: PLC0415

            row = project_service.get_project_by_slug(slug)
            if row is None:
                return None, f"unknown sqlite_project_slug={slug!r} — not in SQLite project registry"
            return int(row["id"]), None
        except Exception as exc:
            return None, f"sqlite_project_slug lookup failed: {type(exc).__name__}: {exc}"

    base = sqlite_project_id or _sqlite_project_id_for(source, projects_index_entry)
    return (base if base is not None else 1), None


def import_to_sqlite(
    task: dict,
    project_id: int,
    dry_run: bool,
    source_label: str,
) -> tuple[str, str]:
    """
    Import a tasks.json task into the SQLite task queue.

    Returns (new_status, message):
      "imported"  — created in SQLite; tasks.json entry will be marked "imported"
      "blocked"   — could not import; tasks.json entry will be marked "blocked"
    """
    if not _SQLITE_AVAILABLE:
        return "blocked", "SQLite services unavailable — cannot import"

    if dry_run:
        return "imported", f"[DRY-RUN] would import to SQLite project_id={project_id}"

    try:
        import task_service  # noqa: PLC0415

        title = task.get("title") or task.get("description") or str(task.get("task_id", "untitled"))
        action_type = task.get("action_type", "log_only")
        payload = task.get("action_payload") or {}

        # Build a human-readable description that preserves the payload so the
        # SQLite worker has full context when building the prompt.
        if action_type == "claude_execute":
            description = payload.get("prompt", "")
        else:
            description = f"[{action_type}] {json.dumps(payload)}"

        exec_mode = str(task.get("execution_mode", "")).strip().lower()
        if exec_mode == "manual" or task.get("prefer_manual") is True:
            description = (
                "[Operator: run execution worker with --mode manual — no API key required]\n\n"
                + (description or "")
            )

        raw_priority = task.get("priority", 3)
        priority = _PRIORITY_MAP.get(int(raw_priority), "normal") if isinstance(raw_priority, int) else "normal"

        # Avoid re-importing if a task with the same title already exists in this project.
        existing = [
            t for t in task_service.list_tasks(project_id=project_id)
            if t["title"] == title and t["source"] == "import"
        ]
        if existing:
            return "imported", f"already in SQLite (id={existing[0]['id']})"

        new_task = task_service.create_task(
            project_id=project_id,
            title=title,
            description=description or None,
            status="pending",
            priority=priority,
            task_type="other",
            source="import",
        )
        return "imported", f"created SQLite task id={new_task['id']}"

    except Exception as exc:
        return "blocked", f"import failed: {type(exc).__name__}: {exc}"


# ── JSON helpers ──────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict | list:
    with path.open() as f:
        return json.load(f)


def save_json(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


# ── State ─────────────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        return load_json(STATE_FILE)
    return {"last_run": None, "processed_tasks": {}}


def save_state(state: dict) -> None:
    save_json(STATE_FILE, state)


def already_processed(state: dict, source: str, task_id: str) -> bool:
    return task_id in state.get("processed_tasks", {}).get(source, {})


def record_result(state: dict, source: str, task_id: str, outcome: dict) -> None:
    state.setdefault("processed_tasks", {}).setdefault(source, {})
    state["processed_tasks"][source][task_id] = outcome


# ── Safety: path confinement ──────────────────────────────────────────────────

def resolve_tasks_json_path(project_path: Path) -> Path:
    """Prefer `.claude/tasks.json`; fall back to project root `tasks.json`."""
    claude_tasks = project_path / ".claude" / "tasks.json"
    if claude_tasks.is_file():
        return claude_tasks
    return project_path / "tasks.json"


def safe_path(project_path: Path, relative: str) -> Path:
    resolved = (project_path / relative).resolve()
    if not str(resolved).startswith(str(project_path.resolve())):
        raise ValueError(
            f"Path escape blocked: '{relative}' resolves outside '{project_path}'"
        )
    return resolved


# ── Action handlers ───────────────────────────────────────────────────────────

class ActionError(Exception):
    pass


def _handle_ingest_action(
    action_type: str,
    payload: dict,
    project_id: int,
    dry_run: bool,
) -> tuple[str, str]:
    """Persist structured data via service layer. Returns (status, message)."""
    if not _SQLITE_AVAILABLE:
        return "blocked", "SQLite services unavailable — cannot ingest"
    if dry_run:
        return "complete", f"[DRY-RUN] would {action_type} project_id={project_id}"

    try:
        if action_type == "ingest_blueprint":
            import blueprint_service  # noqa: PLC0415

            title = str(payload.get("title", "")).strip()
            content = str(payload.get("content", "")).strip()
            if not title or not content:
                return "blocked", "ingest_blueprint requires payload.title and payload.content"
            blueprint_service.create(
                project_id,
                str(payload.get("type", "prd")).strip() or "prd",
                title,
                content,
                version=int(payload.get("version", 1)),
            )
            return "complete", f"ingested blueprint for project_id={project_id}"

        if action_type == "ingest_decision":
            import decision_service  # noqa: PLC0415

            title = str(payload.get("title", "")).strip()
            content = str(payload.get("content", "")).strip()
            if not title or not content:
                return "blocked", "ingest_decision requires payload.title and payload.content"
            decision_service.add_decision(title, content, project_id=project_id)
            return "complete", f"ingested decision for project_id={project_id}"

        if action_type == "ingest_memory":
            import memory_service  # noqa: PLC0415

            key = str(payload.get("key", "")).strip()
            value = payload.get("value")
            if not key or value is None:
                return "blocked", "ingest_memory requires payload.key and payload.value"
            memory_service.upsert_memory(project_id, key, str(value))
            return "complete", f"ingested memory key={key!r} project_id={project_id}"

        if action_type == "ingest_session_log":
            import session_log_service  # noqa: PLC0415

            session_date = str(payload.get("session_date", "")).strip()
            if not session_date:
                return "blocked", "ingest_session_log requires payload.session_date"
            session_log_service.create(
                project_id,
                session_date,
                agent=payload.get("agent"),
                scope_active=payload.get("scope_active"),
                tasks_completed=payload.get("tasks_completed"),
                next_task=payload.get("next_task"),
                git_state=payload.get("git_state"),
                open_issues=payload.get("open_issues"),
                notes=payload.get("notes"),
            )
            return "complete", f"ingested session_log for project_id={project_id}"

        return "blocked", f"unknown ingest action: {action_type!r}"
    except Exception as exc:
        return "blocked", f"{action_type} failed: {type(exc).__name__}: {exc}"


def handle_log_only(payload: dict, project_path: Path | None) -> str:
    msg = payload.get("message", "").strip()
    if not msg:
        raise ActionError("payload.message is required for log_only")
    return msg


def handle_run_script(payload: dict, project_path: Path | None) -> str:
    if project_path is None:
        raise ActionError("run_script requires a project_path")

    script_rel = payload.get("script", "").strip()
    if not script_rel:
        raise ActionError("payload.script is required for run_script")

    script_abs = safe_path(project_path, script_rel)
    if not script_abs.exists():
        raise ActionError(f"Script not found: {script_abs}")

    args = payload.get("args", [])
    timeout = int(payload.get("timeout_seconds", 60))
    cmd = [str(script_abs)] + [str(a) for a in args]

    result = subprocess.run(
        cmd, capture_output=True, text=True,
        timeout=timeout, cwd=str(project_path),
    )
    if result.returncode != 0:
        raise ActionError(
            f"Script exited {result.returncode}: {result.stderr.strip()[:500]}"
        )
    return result.stdout.strip()[:500] or "(no stdout)"


def handle_generate_file(payload: dict, project_path: Path | None) -> str:
    if project_path is None:
        raise ActionError("generate_file requires a project_path")

    rel_path = payload.get("path", "").strip()
    content = payload.get("content")
    overwrite = payload.get("overwrite", True)

    if not rel_path:
        raise ActionError("payload.path is required for generate_file")
    if content is None:
        raise ActionError("payload.content is required for generate_file")

    dest = safe_path(project_path, rel_path)
    if dest.exists() and not overwrite:
        return f"Skipped — file already exists: {rel_path}"

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(textwrap.dedent(str(content)))
    return f"Written {dest.stat().st_size} bytes → {rel_path}"


def handle_claude_execute(payload: dict, project_path: Path | None, task: dict | None = None) -> str:
    """Send a prompt to Claude Code CLI for autonomous execution."""
    prompt = payload.get("prompt", "").strip()
    if not prompt:
        raise ActionError("payload.prompt is required for claude_execute")

    # Inject correlation_id so Claude can thread related tasks together
    correlation_id = (task or {}).get("correlation_id", "")
    if correlation_id:
        prompt = f"[correlation_id: {correlation_id}]\n\n{prompt}"

    cwd = str(project_path) if project_path else str(Path.home())
    timeout = int(payload.get("timeout_seconds", 300))

    try:
        result = subprocess.run(
            ["claude", "--print", "--prompt", prompt],
            capture_output=True, text=True,
            timeout=timeout, cwd=cwd,
        )
        if result.returncode == 0:
            return result.stdout.strip()[:500]
        return f"exit {result.returncode}: {result.stderr.strip()[:200]}"
    except subprocess.TimeoutExpired:
        raise ActionError(f"Claude CLI timed out after {timeout}s")
    except FileNotFoundError:
        raise ActionError("claude CLI not found — is Claude Code installed?")


def handle_run_plan(payload: dict, project_path: Path | None) -> str:
    """Invoke the orchestrator with a named plan."""
    plan_name = payload.get("plan", "").strip()
    goal = payload.get("goal", "").strip()
    if not plan_name:
        raise ActionError("payload.plan is required for run_plan")
    if not goal:
        raise ActionError("payload.goal is required for run_plan")

    runs_dir = payload.get("runs_dir") or str(Path.home() / "agent-services" / "runs")
    mode = payload.get("mode", "simulate")

    cmd = [
        "python3", "-m", "orchestrator",
        "--runs-dir", runs_dir,
        "--plan", plan_name,
        "--goal", goal,
        "--mode", mode,
    ]
    cwd = str(Path.home() / ".claude")
    timeout = int(payload.get("timeout_seconds", 600))

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=cwd,
        )
        output = result.stdout.strip()[:500] or f"exit {result.returncode}"
        if result.returncode != 0:
            raise ActionError(f"Orchestrator exited {result.returncode}: {result.stderr.strip()[:200]}")
        return output
    except subprocess.TimeoutExpired:
        raise ActionError(f"Orchestrator timed out after {timeout}s")


# ── Task dispatch ─────────────────────────────────────────────────────────────

def dispatch(
    task: dict,
    project_path: Path | None,
    sqlite_project_id: int | None,
    projects_index_entry: dict | None,
    source: str,
    dry_run: bool,
) -> tuple[str, str]:
    """
    Route one task:
    - log_only   → execute inline (no SQLite, no AI needed)
    - everything else → import to SQLite for the SQLite worker to execute
    """
    action_type = task.get("action_type", "log_only")
    action_payload = task.get("action_payload") or {}

    if action_type == "log_only":
        if dry_run:
            return "complete", "[DRY-RUN] log_only — would record message"
        try:
            result = handle_log_only(action_payload, project_path)
            return "complete", result
        except ActionError as e:
            return "blocked", str(e)

    pid, perr = _final_sqlite_project_id(
        task,
        sqlite_project_id=sqlite_project_id,
        source=source,
        projects_index_entry=projects_index_entry,
    )
    if perr:
        return "blocked", perr
    assert pid is not None

    if action_type in (
        "ingest_blueprint",
        "ingest_decision",
        "ingest_memory",
        "ingest_session_log",
    ):
        return _handle_ingest_action(action_type, action_payload, pid, dry_run)

    # Default: import execution-style tasks to SQLite queue
    return import_to_sqlite(task, pid, dry_run, source)


# ── Process a task list ───────────────────────────────────────────────────────

def process_tasks(
    source: str,
    tasks_path: Path,
    project_path: Path | None,
    sqlite_project_id: int | None,
    projects_index_entry: dict | None,
    state: dict,
    dry_run: bool,
) -> dict:
    stats = {"processed": 0, "complete": 0, "imported": 0, "blocked": 0, "skipped": 0, "already_done": 0}

    if not tasks_path.exists():
        log(source, "WARN", f"tasks.json not found at {tasks_path}", dry_run=dry_run)
        return stats

    tasks = load_json(tasks_path)
    if not isinstance(tasks, list):
        log(source, "ERROR", "tasks.json is not a JSON array", dry_run=dry_run)
        return stats

    pending = [t for t in tasks if t.get("status") not in ("complete", "blocked", "imported")]
    log(source, "INFO", f"{len(pending)} pending / {len(tasks)} total", dry_run=dry_run)

    pending.sort(key=lambda t: (t.get("priority", 999), t.get("created_at", "")))

    for task in pending:
        task_id = task.get("task_id") or task.get("id")
        if not task_id:
            title = task.get("title", task.get("description", "?"))
            log(source, "WARN", f"Task missing ID — skipping: {title}", dry_run=dry_run)
            stats["skipped"] += 1
            continue

        if already_processed(state, source, task_id):
            stats["already_done"] += 1
            continue

        action_type = task.get("action_type", "log_only")
        title = task.get("title", task.get("description", task_id))
        log(source, "INFO", f"Processing: {title}",
            task_id=task_id, action_type=action_type, dry_run=dry_run)

        new_status, result_msg = dispatch(
            task, project_path, sqlite_project_id, projects_index_entry, source, dry_run
        )

        level = "INFO" if new_status in ("complete", "imported") else "ERROR"
        log(source, level, f"Task {new_status}: {result_msg}",
            task_id=task_id, action_type=action_type, result=new_status, dry_run=dry_run)

        if not dry_run:
            for i, t in enumerate(tasks):
                tid = t.get("task_id") or t.get("id")
                if tid == task_id:
                    tasks[i]["status"] = new_status
                    tasks[i]["updated_at"] = now_iso()
                    if new_status == "complete":
                        tasks[i]["completed_at"] = now_iso()
                    break

            record_result(state, source, task_id, {
                "status": new_status,
                "action_type": action_type,
                "result": result_msg,
                "ts": now_iso(),
            })

        stats["processed"] += 1
        if new_status == "complete":
            stats["complete"] += 1
        elif new_status == "imported":
            stats["imported"] += 1
        else:
            stats["blocked"] += 1

    if stats["processed"] > 0 and not dry_run:
        save_json(tasks_path, tasks)
        log(source, "INFO", f"Saved ({stats['processed']} updated)", dry_run=dry_run)

    return stats


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    # No validate_env() — this worker no longer executes AI tasks directly.
    # API key is only needed by the SQLite worker (system/services/task_worker.py).

    parser = argparse.ArgumentParser(description="Global task worker (import-only)")
    parser.add_argument("--dry-run", action="store_true", help="Preview only — no writes")
    parser.add_argument("--project", metavar="ID", help="Process one project only")
    parser.add_argument("--global-only", action="store_true", help="Only process ~/.claude/tasks.json")
    args = parser.parse_args()

    state = load_state()
    all_stats = {}

    # 1. Global tasks (~/.claude/tasks.json)
    if not args.project:
        log("global", "INFO", "=== Global tasks ===", dry_run=args.dry_run)
        sqlite_pid = _sqlite_project_id_for("global", None)
        all_stats["global"] = process_tasks(
            "global", GLOBAL_TASKS, None, sqlite_pid, None, state, args.dry_run
        )

    # 2. Per-project tasks
    if not args.global_only:
        if PROJECTS_INDEX.exists():
            index = load_json(PROJECTS_INDEX)
            projects = index.get("projects", [])

            if args.project:
                projects = [p for p in projects if p["project_id"] == args.project]
                if not projects:
                    print(f"ERROR: project '{args.project}' not in registry", file=sys.stderr)
                    sys.exit(1)

            active = [p for p in projects if p.get("status") == "active"]

            for project in active:
                pid = project["project_id"]
                ppath = Path(project["project_path"])
                tasks_file = resolve_tasks_json_path(ppath)
                sqlite_pid = _sqlite_project_id_for(pid, project)

                log(pid, "INFO", f"=== {project['project_name']} ===", dry_run=args.dry_run)
                all_stats[pid] = process_tasks(
                    pid, tasks_file, ppath, sqlite_pid, project, state, args.dry_run
                )
                _kind, _msg = sync_project_md_blueprint(ppath, sqlite_pid, args.dry_run)
                if _kind not in ("skipped", "unchanged"):
                    log(pid, "INFO", f"project.md → dashboard: {_msg}", dry_run=args.dry_run)
        else:
            log("_system", "WARN", f"No projects_index.json at {PROJECTS_INDEX}", dry_run=args.dry_run)

    if not args.dry_run:
        state["last_run"] = now_iso()
        save_state(state)

    log("_system", "INFO", f"Worker finished — {json.dumps(all_stats)}", dry_run=args.dry_run)


if __name__ == "__main__":
    main()
