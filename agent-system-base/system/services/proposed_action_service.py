from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import db
import task_service


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_action(row: Any) -> dict[str, Any]:
    d = dict(row)
    try:
        d["payload"] = json.loads(d["payload"])
    except (json.JSONDecodeError, TypeError):
        pass
    return d


def propose(
    action_type: str,
    payload: dict[str, Any],
    *,
    created_by: str | None = None,
    project_id: int | None = None,
) -> dict[str, Any]:
    """
    Store an AI-proposed action for human review.

    action_type must be one of: 'create_task', 'update_task', 'other'
    payload is the action data (stored as JSON).
    """
    valid_types = {"create_task", "update_task", "other"}
    if action_type not in valid_types:
        raise ValueError(f"invalid action_type: {action_type!r}")

    now = _iso_now()
    payload_json = json.dumps(payload)
    with db.connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO proposed_actions (type, payload, status, created_by, created_at, project_id)
            VALUES (?, ?, 'pending', ?, ?, ?) RETURNING id
            """,
            (action_type, payload_json, created_by, now, project_id),
        )
        aid = cur.lastrowid
        conn.commit()
        row = conn.execute("SELECT * FROM proposed_actions WHERE id = ?", (aid,)).fetchone()
        assert row is not None
        return _row_to_action(row)


def list_pending(*, project_id: int | None = None) -> list[dict[str, Any]]:
    """Return actions with status='pending', oldest first."""
    with db.connect() as conn:
        if project_id is not None:
            rows = conn.execute(
                """
                SELECT * FROM proposed_actions
                WHERE status = 'pending' AND project_id = ?
                ORDER BY created_at ASC, id ASC
                """,
                (project_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM proposed_actions
                WHERE status = 'pending'
                ORDER BY created_at ASC, id ASC
                """
            ).fetchall()
        return [_row_to_action(r) for r in rows]


def list_all(*, project_id: int | None = None) -> list[dict[str, Any]]:
    """Return all actions regardless of status, newest first."""
    with db.connect() as conn:
        if project_id is not None:
            rows = conn.execute(
                """
                SELECT * FROM proposed_actions
                WHERE project_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (project_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM proposed_actions ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [_row_to_action(r) for r in rows]


def get_action(action_id: int) -> dict[str, Any] | None:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM proposed_actions WHERE id = ?", (action_id,)
        ).fetchone()
        return _row_to_action(row) if row else None


def approve(action_id: int) -> dict[str, Any]:
    """
    Approve a pending action and execute it via the appropriate service.

    For 'create_task': calls task_service.create_task() with payload fields.
    For 'update_task': calls task_service.update_status() with payload fields.
    For 'other':       marks approved without side effects.

    Raises LookupError if action not found.
    Raises ValueError if action is not pending.
    """
    action = get_action(action_id)
    if action is None:
        raise LookupError(f"proposed action not found: {action_id}")
    if action["status"] != "pending":
        raise ValueError(f"action {action_id} is already {action['status']!r}")

    payload = action["payload"] if isinstance(action["payload"], dict) else {}

    try:
        if action["type"] == "create_task":
            task_service.create_task(
                project_id=int(payload["project_id"]),
                title=payload["title"],
                description=payload.get("description"),
                status=payload.get("status", "pending"),
                priority=payload.get("priority", "normal"),
                task_type=payload.get("type", "chore"),
                source=payload.get("source", "api"),
            )
        elif action["type"] == "update_task":
            task_service.update_status(
                int(payload["task_id"]),
                payload["status"],
            )
        # 'other' has no side effect — recorded only

        now = _iso_now()
        with db.connect() as conn:
            conn.execute(
                "UPDATE proposed_actions SET status = 'approved', reviewed_at = ? WHERE id = ?",
                (now, action_id),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM proposed_actions WHERE id = ?", (action_id,)
            ).fetchone()
            return _row_to_action(row)  # type: ignore[return-value]

    except Exception as exc:
        # Execution failed — mark rejected so it doesn't linger as pending
        now = _iso_now()
        with db.connect() as conn:
            conn.execute(
                """
                UPDATE proposed_actions
                SET status = 'rejected', reviewed_at = ?, review_note = ?
                WHERE id = ?
                """,
                (now, f"approve failed: {exc}", action_id),
            )
            conn.commit()
        raise


def reject(action_id: int, *, note: str | None = None) -> dict[str, Any]:
    """
    Reject a pending action.

    Raises LookupError if action not found.
    Raises ValueError if action is not pending.
    """
    action = get_action(action_id)
    if action is None:
        raise LookupError(f"proposed action not found: {action_id}")
    if action["status"] != "pending":
        raise ValueError(f"action {action_id} is already {action['status']!r}")

    now = _iso_now()
    with db.connect() as conn:
        conn.execute(
            """
            UPDATE proposed_actions
            SET status = 'rejected', reviewed_at = ?, review_note = ?
            WHERE id = ?
            """,
            (now, note, action_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM proposed_actions WHERE id = ?", (action_id,)
        ).fetchone()
        return _row_to_action(row)  # type: ignore[return-value]
