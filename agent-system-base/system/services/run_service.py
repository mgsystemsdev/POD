from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import db
import task_service

_STATUSES = frozenset({"pending", "pending_input", "running", "success", "failed", "cancelled"})
_TERMINAL = frozenset({"success", "failed", "cancelled"})
_MODES = frozenset({"manual", "ai"})


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _validate_status(value: str) -> None:
    if value not in _STATUSES:
        raise ValueError(f"invalid status: {value!r}")


def _serialize_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, separators=(",", ":"), default=str)


def _row_to_run(row: Any) -> dict[str, Any]:
    d = dict(row)
    return {
        "id": d["id"],
        "task_id": d["task_id"],
        "mode": d["mode"],
        "status": d["status"],
        "input_prompt": d["input_prompt"],
        "output": d["output"],
        "started_at": d["started_at"],
        "completed_at": d["completed_at"],
        "error_message": d["error_message"],
        # agent is legacy read-only — excluded from return dict
    }


def _assert_legal_transition(current: str, new: str) -> None:
    if current in _TERMINAL:
        raise ValueError(f"illegal transition: run is terminal ({current!r})")
    if current == "pending":
        if new not in ("running", "pending_input"):
            raise ValueError(
                f"illegal transition: pending → {new!r} (expected 'running' or 'pending_input')"
            )
    elif current == "pending_input":
        if new != "running":
            raise ValueError(
                f"illegal transition: pending_input → {new!r} (expected 'running')"
            )
    elif current == "running":
        if new not in _TERMINAL:
            raise ValueError(
                f"illegal transition: running → {new!r} (expected terminal status)"
            )


def create_run(task_id: int, *, mode: str = "ai") -> dict[str, Any]:
    if mode not in _MODES:
        raise ValueError(f"invalid mode: {mode!r}")
    now = _iso_now()
    with db.connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO runs (task_id, mode, status, input_prompt, output, agent, started_at, completed_at, error_message)
            VALUES (?, ?, 'pending', NULL, NULL, NULL, ?, NULL, NULL) RETURNING id
            """,
            (task_id, mode, now),
        )
        rid = cur.lastrowid
        conn.commit()
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (rid,)).fetchone()
        assert row is not None
        return _row_to_run(row)


def update_run(
    run_id: int,
    status: str,
    *,
    output: Any = None,
    error: Any = None,
    input_prompt: str | None = None,
) -> dict[str, Any] | None:
    _validate_status(status)

    if status == "failed" and error is None:
        raise ValueError("failed runs require error")

    if status == "success" and error is not None:
        raise ValueError("error must be None when status is 'success'")

    if status not in _TERMINAL and error is not None:
        raise ValueError(f"error must be None when status is {status!r}")

    if input_prompt is not None and status != "pending_input":
        raise ValueError("input_prompt may only be set when transitioning to 'pending_input'")

    now = _iso_now()

    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            conn.rollback()
            return None

        current = row["status"]
        _assert_legal_transition(current, status)

        if status in _TERMINAL and row["completed_at"] is not None:
            conn.rollback()
            raise ValueError("completed_at already set; terminal run is immutable")

        if status == "success":
            new_error_message: str | None = None
            new_output = _serialize_text(output) if output is not None else row["output"]
            new_completed_at = now
            new_input_prompt = row["input_prompt"]
        elif status == "failed":
            new_error_message = _serialize_text(error)
            new_output = _serialize_text(output) if output is not None else row["output"]
            new_completed_at = now
            new_input_prompt = row["input_prompt"]
        elif status == "cancelled":
            new_error_message = _serialize_text(error) if error is not None else None
            new_output = _serialize_text(output) if output is not None else row["output"]
            new_completed_at = now
            new_input_prompt = row["input_prompt"]
        elif status == "pending_input":
            new_error_message = None
            new_output = row["output"]
            new_completed_at = None
            new_input_prompt = input_prompt  # store the prepared prompt
        else:
            # running
            new_error_message = None
            new_output = row["output"]
            new_completed_at = None
            new_input_prompt = row["input_prompt"]

        conn.execute(
            """
            UPDATE runs
            SET
              status = ?,
              input_prompt = ?,
              output = ?,
              completed_at = ?,
              error_message = ?
            WHERE id = ?
            """,
            (status, new_input_prompt, new_output, new_completed_at, new_error_message, run_id),
        )
        conn.commit()
        fresh = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        assert fresh is not None
        return _row_to_run(fresh)


def get_runs_for_task(task_id: int) -> list[dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM runs
            WHERE task_id = ?
            ORDER BY started_at DESC, id DESC
            """,
            (task_id,),
        ).fetchall()
        return [_row_to_run(r) for r in rows]


def list_recent_runs(*, project_id: int | None = None, limit: int = 500) -> list[dict[str, Any]]:
    """All runs newest first, optionally scoped to a project via tasks.project_id."""
    lim = max(1, min(int(limit), 2000))
    with db.connect() as conn:
        if project_id is not None:
            rows = conn.execute(
                """
                SELECT r.* FROM runs r
                INNER JOIN tasks t ON t.id = r.task_id
                WHERE t.project_id = ?
                ORDER BY r.started_at DESC, r.id DESC
                LIMIT ?
                """,
                (project_id, lim),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM runs
                ORDER BY started_at DESC, id DESC
                LIMIT ?
                """,
                (lim,),
            ).fetchall()
        return [_row_to_run(r) for r in rows]


def complete_manual_run(run_id: int, output: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Complete a manual run with correct state ordering.

    Validates run is pending_input, then:
      1. run → running
      2. task → done   (FIRST)
      3. run → success (SECOND)

    Returns (task, run).
    """
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise ValueError(f"run {run_id} not found")
        if row["status"] != "pending_input":
            raise ValueError(
                f"run {run_id} is not pending_input (current: {row['status']!r})"
            )
        task_id = int(row["task_id"])

    # Step 1: pending_input → running
    update_run(run_id, "running")

    # Step 2: task → done FIRST
    task = task_service.update_status(task_id, "done")

    # Step 3: run → success SECOND
    run = update_run(run_id, "success", output=output)

    assert task is not None
    assert run is not None
    return task, run
