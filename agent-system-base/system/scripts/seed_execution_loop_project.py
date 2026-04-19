#!/usr/bin/env python3
"""
Idempotently add the Execution Loop checklist tasks to **Global Claude** (`claude-global`).

Run from anywhere, after sync:
  python3 ~/agents/agent-system-base/system/scripts/seed_execution_loop_project.py

Uses the same DB as system/services/db.py (see DATABASE_PATH there).
"""
from __future__ import annotations

import sys
from pathlib import Path

_SERVICES = Path(__file__).resolve().parent.parent / "services"
sys.path.insert(0, str(_SERVICES))

import project_service  # noqa: E402
import task_service  # noqa: E402

PROJECT_NAME = "Global Claude"
PROJECT_SLUG = "claude-global"

TASKS: list[tuple[str, str, str]] = [
    (
        "Execution Loop / Runtime: Set working directory to runtime environment",
        "Change the current directory to `~/agents/agent-services` before executing any system commands",
        "Commands executed from this directory resolve system modules without import errors",
    ),
    (
        "Execution Loop / Dashboard: Start FastAPI server",
        "Run `python3 system/dashboard/server.py` from the runtime directory",
        "Server starts without error and binds to `127.0.0.1:8765`",
    ),
    (
        "Execution Loop / Dashboard: Verify dashboard availability",
        "Open `http://127.0.0.1:8765` in a browser",
        "Dashboard loads and displays existing projects and tasks",
    ),
    (
        "Execution Loop / Worker: Execute manual task worker",
        "Run `python3 system/services/task_worker.py --mode manual` from the runtime directory",
        "Terminal outputs `READY task_id=... run_id=...`",
    ),
    (
        "Execution Loop / State: Validate task claim and run creation",
        "Check via dashboard or API that the claimed task status is `in_progress` and the run status is `pending_input` with a non-empty prompt",
        "Task is `in_progress` and run is `pending_input` with populated `input_prompt`",
    ),
    (
        "Execution Loop / External Execution: Execute generated prompt",
        "Copy the `input_prompt` and execute it in an external tool (Claude or Cursor)",
        "A complete output is produced from the prompt",
    ),
    (
        "Execution Loop / Completion: Submit task completion via API",
        "Send a POST request to `/api/tasks/{task_id}/complete` with the execution output as a plain text body",
        "Request succeeds and the system accepts the output",
    ),
    (
        "Execution Loop / Completion Policy: Define output-preserving completion requirement",
        "Treat completion via API with a plain text body as required for any task where execution output must be preserved as part of the run record",
        "Tasks requiring output preservation are completed with non-placeholder output stored in the run",
    ),
    (
        "Execution Loop / Completion Policy: Allow administrative completion via dashboard",
        "Allow use of the dashboard “Done” action (no request body) only for cases where output preservation is not required",
        "Tasks completed via dashboard without body are explicitly recognized as administrative completions with placeholder output",
    ),
    (
        "Execution Loop / State: Validate completion",
        "Verify that the task status is `done` and the run status is `success`, and output is stored",
        "Task is `done`, run is `success`, and output field is populated",
    ),
]


def main() -> int:
    proj = project_service.get_project_by_slug(PROJECT_SLUG)
    if proj is None:
        proj = project_service.create_project(PROJECT_NAME, PROJECT_SLUG)
        print(f"Created project {proj['id']}: {PROJECT_NAME} ({PROJECT_SLUG})")
    else:
        print(f"Using existing project {proj['id']}: {PROJECT_NAME} ({PROJECT_SLUG})")

    pid = int(proj["id"])
    existing = {t["title"] for t in task_service.list_tasks(project_id=pid)}
    added = 0
    for title, desc, success in TASKS:
        if title in existing:
            continue
        body = f"{desc}\n\n**Success criteria:** {success}"
        task_service.create_task(
            pid,
            title,
            description=body,
            status="pending",
            priority="high",
            task_type="chore",
            source="manual",
        )
        added += 1
        print(f"  + task: {title[:60]}…")

    if added == 0:
        print("All checklist tasks already present; nothing to add.")
    else:
        print(f"Added {added} task(s). Filter the dashboard by project “{PROJECT_NAME}”.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
