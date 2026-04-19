#!/usr/bin/env python3
"""
Task worker: claims and prepares or executes exactly one pending task.

Manual mode (default, no API key required):
  - Claims one task, builds prompt, stores in runs.input_prompt, sets run →
    pending_input, prints "READY task_id=N run_id=N", exits 0.
  - Human copies prompt from dashboard, executes in Claude/Cursor, submits
    result via POST /api/tasks/{id}/complete.

AI mode (requires ANTHROPIC_API_KEY):
  - Claims one task, executes via Claude Messages API, stores output, closes
    run and task.

Uses task_service, run_service, context_loader, claude_prompts, claude_execution
only — no sqlite3, db, or direct SQL.

Recovery at startup:
  - _recover_stuck_tasks: resets in_progress tasks older than threshold → pending
  - _recover_stuck_runs: closes running runs whose task is already done → success
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

import claude_execution
import claude_prompts
import context_loader
import run_service
import task_service

_STUCK_THRESHOLD_MINUTES = 30


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _recover_stuck_tasks(project_id: int | None) -> int:
    """Reset in_progress tasks older than STUCK_THRESHOLD_MINUTES back to pending."""
    cutoff = (
        datetime.now(timezone.utc) - timedelta(minutes=_STUCK_THRESHOLD_MINUTES)
    ).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    stuck = task_service.list_tasks(project_id=project_id, status="in_progress")
    recovered = 0
    for task in stuck:
        if str(task["updated_at"]) < cutoff:
            task_service.update_status(int(task["id"]), "pending")
            recovered += 1
    return recovered


def _recover_stuck_runs(project_id: int | None) -> int:
    """Close running runs whose task is already done.

    If complete_manual_run set task → done but crashed before run → success,
    the run is left in 'running'. Recover by closing it to success.
    This is idempotent — runs already terminal are skipped by update_run.
    """
    tasks_done = task_service.list_tasks(project_id=project_id, status="done")
    recovered = 0
    for task in tasks_done:
        for run in run_service.get_runs_for_task(int(task["id"])):
            if run["status"] == "running":
                try:
                    run_service.update_run(int(run["id"]), "success", output="recovered")
                    recovered += 1
                except ValueError:
                    pass  # already terminal — nothing to do
    return recovered


def _build_prompt(task: dict[str, Any]) -> str:
    pid = int(task["project_id"])
    ctx = context_loader.load_project_context(project_id=pid)
    rules = context_loader.load_rules_context(ctx.get("root"))
    system, user = claude_prompts.build_prompts(task, ctx, rules=rules)
    return f"SYSTEM:\n{system}\n\nUSER:\n{user}"


def _execute_claude(task: dict[str, Any]) -> str:
    pid = int(task["project_id"])
    ctx = context_loader.load_project_context(project_id=pid)
    rules = context_loader.load_rules_context(ctx.get("root"))
    system, user = claude_prompts.build_prompts(task, ctx, rules=rules)
    return claude_execution.run_messages_with_retry(system, user)


def _fail_run_and_task(run_id: int, task_id: int, error: str) -> None:
    """Best-effort: mark run failed, then block task only if run was successfully failed."""
    run_failed = False
    try:
        run_service.update_run(run_id, "running")
    except ValueError:
        pass
    try:
        run_service.update_run(run_id, "failed", error=error)
        run_failed = True
    except ValueError:
        pass
    if run_failed:
        task_service.update_status(task_id, "blocked")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Claim and prepare (manual) or execute (ai) one pending task.",
    )
    parser.add_argument(
        "--project-id",
        type=int,
        default=None,
        help="Only consider tasks for this project. Omit to process all projects.",
    )
    parser.add_argument(
        "--mode",
        choices=["manual", "ai"],
        default="manual",
        help="manual: prepare prompt and stop (default). ai: execute via Claude API.",
    )
    args = parser.parse_args(argv)

    if args.mode == "ai" and not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        print(
            "Skipping: --mode ai requires ANTHROPIC_API_KEY. "
            "Use --mode manual (default) to queue prompts without the API, or set the key.",
            file=sys.stderr,
        )
        return 2

    # Recovery: reset stuck tasks and close orphaned running runs.
    recovered_tasks = _recover_stuck_tasks(args.project_id)
    if recovered_tasks:
        print(f"Recovered {recovered_tasks} stuck in_progress task(s) → pending")

    recovered_runs = _recover_stuck_runs(args.project_id)
    if recovered_runs:
        print(f"Recovered {recovered_runs} stuck running run(s) → success")

    task = task_service.claim_next_pending(project_id=args.project_id)
    if task is None:
        print("No pending tasks")
        return 0

    task_id = int(task["id"])

    if args.mode == "manual":
        run = run_service.create_run(task_id, mode="manual")
        run_id = int(run["id"])
        try:
            prompt = _build_prompt(task)
            run_service.update_run(run_id, "pending_input", input_prompt=prompt)
            print(f"READY  task_id={task_id}  run_id={run_id}")
            return 0
        except (KeyboardInterrupt, SystemExit):
            _fail_run_and_task(run_id, task_id, "Interrupted")
            print(
                f"\nInterrupted — task_id={task_id} blocked, run_id={run_id} failed",
                file=sys.stderr,
            )
            raise
        except Exception as e:
            err = str(e)
            _fail_run_and_task(run_id, task_id, err)
            print(f"ERR task_id={task_id} run_id={run_id}: {err[:120]}", file=sys.stderr)
            return 1

    else:
        # AI mode: claim, execute, close.
        run = run_service.create_run(task_id, mode="ai")
        run_id = int(run["id"])
        try:
            run_service.update_run(run_id, "running")
            text = _execute_claude(task)
            task_service.update_status(task_id, "done")
            run_service.update_run(run_id, "success", output=text)
            print(f"OK  task_id={task_id} run_id={run_id}")
            return 0

        except (KeyboardInterrupt, SystemExit):
            _fail_run_and_task(run_id, task_id, "Interrupted")
            print(
                f"\nInterrupted — task_id={task_id} blocked, run_id={run_id} failed",
                file=sys.stderr,
            )
            raise

        except Exception as e:
            err = str(e)
            _fail_run_and_task(run_id, task_id, err)
            print(f"ERR task_id={task_id} run_id={run_id}: {err[:120]}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    sys.exit(main())
