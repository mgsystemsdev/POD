#!/usr/bin/env python3
"""
Task Dashboard — SQLite execution system API + static HTML.

Run:  cd ~/agents/agent-services && python3 system/dashboard/server.py
Open: http://localhost:8765
"""

from __future__ import annotations

import hmac
import logging
import os
import sys
from pathlib import Path
from typing import Any, List, Optional

# ── Service path ──────────────────────────────────────────────────────────────
_SERVICES_DIR = Path(__file__).resolve().parent.parent / "services"
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

import approval_service  # noqa: E402
import auxiliary_agent_output_service  # noqa: E402
import backlog_service  # noqa: E402
import blueprint_service  # noqa: E402
import decision_service  # noqa: E402
import memory_service  # noqa: E402
import project_service  # noqa: E402
import proposed_action_service  # noqa: E402
import run_service  # noqa: E402
import session_log_service  # noqa: E402
import task_service  # noqa: E402
import validation_service  # noqa: E402

import uvicorn
from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# ── Paths ──────────────────────────────────────────────────────────────────────
LOG_DIR = Path(os.environ.get("LOG_DIR", str(Path.home() / "agents" / "agent-services" / "logs")))
LOG_FILE = LOG_DIR / "dashboard.log"
HTML_FILE = Path(__file__).resolve().parent / "index.html"

# ── Logging ────────────────────────────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
_fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(asctime)s  %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"))

log = logging.getLogger("dashboard")
log.setLevel(logging.INFO)
log.addHandler(_fh)
log.addHandler(logging.StreamHandler())

# ── Dashboard task JSON: DB priority ↔ UI P1–P5 ────────────────────────────────
_DB_TO_UI = {"urgent": 1, "high": 2, "normal": 3, "low": 4}
_UI_TO_DB = {1: "urgent", 2: "high", 3: "normal", 4: "low", 5: "low"}


def _task_out(t: dict) -> dict:
    o = dict(t)
    o["priority"] = _DB_TO_UI.get(str(t.get("priority")), 3)
    return o


def _priority_from_body(p: Any) -> str:
    try:
        n = int(p)
    except (TypeError, ValueError):
        n = 3
    n = max(1, min(5, n))
    return _UI_TO_DB.get(n, "normal")


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)

        expected = os.environ.get("AGENTS_API_KEY", "").strip()
        if not expected:
            return await call_next(request)

        supplied = request.headers.get("X-API-Key", "").strip()
        if not supplied or not hmac.compare_digest(
            supplied.encode("utf-8"), expected.encode("utf-8")
        ):
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)

        return await call_next(request)


# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Task Dashboard", docs_url=None, redoc_url=None)
app.add_middleware(APIKeyMiddleware)


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return HTML_FILE.read_text(encoding="utf-8")


# ── Projects ──────────────────────────────────────────────────────────────────


@app.get("/api/projects")
async def list_projects() -> List[dict]:
    return project_service.list_projects()


@app.post("/api/projects", response_model=None)
async def create_project(body: dict = Body(...)) -> Any:
    name = str(body.get("name", "")).strip()
    slug = str(body.get("slug", "")).strip()
    root_path = body.get("root_path")
    upsert = bool(body.get("upsert"))
    if not name or not slug:
        raise HTTPException(400, "name and slug are required")
    try:
        if upsert:
            row, created = project_service.upsert_project(
                name, slug, root_path=root_path
            )
            return JSONResponse(row, status_code=201 if created else 200)
        return project_service.create_project(name, slug, root_path=root_path)
    except project_service.ProjectSlugConflictError as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.put("/api/projects/{project_id}")
async def update_project(project_id: int, body: dict = Body(...)) -> dict:
    name = body.get("name")
    root_path = body.get("root_path")
    try:
        row = project_service.update_project(
            project_id, name=name, root_path=root_path
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if row is None:
        raise HTTPException(404, "Project not found")
    return row


# ── Tasks ─────────────────────────────────────────────────────────────────────


@app.get("/api/tasks")
async def list_tasks(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
) -> List[dict]:
    rows = task_service.list_tasks(project_id=project_id, status=status)
    return [_task_out(t) for t in rows]


@app.post("/api/tasks")
async def create_task(body: dict = Body(...)) -> dict:
    try:
        pid = int(body["project_id"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(400, "project_id is required") from None
    title = str(body.get("title", "")).strip()
    if not title:
        raise HTTPException(400, "title is required")
    description = body.get("description")
    notes = body.get("notes")
    correlation_id = body.get("correlation_id")
    requirement_ref = body.get("requirement_ref") or None
    decision_id = body.get("decision_id")
    if decision_id is not None:
        try:
            decision_id = int(decision_id)
        except (TypeError, ValueError):
            raise HTTPException(400, "decision_id must be an integer") from None
    p = _priority_from_body(body.get("priority", 3))
    try:
        t = task_service.create_task(
            pid,
            title,
            description=description if description else None,
            priority=p,
            notes=notes if notes else None,
            correlation_id=correlation_id if correlation_id else None,
            requirement_ref=requirement_ref,
            decision_id=decision_id,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _task_out(t)


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: int) -> dict:
    task = task_service.get_task(task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    return _task_out(task)


@app.put("/api/tasks/{task_id}")
async def update_task(task_id: int, body: dict = Body(...)) -> dict:
    if task_service.get_task(task_id) is None:
        raise HTTPException(404, "Task not found")
    title = body.get("title")
    description = body.get("description")
    notes = body.get("notes")
    correlation_id = body.get("correlation_id")
    status = body.get("status")
    priority = None
    if "priority" in body:
        priority = _priority_from_body(body.get("priority"))
    try:
        t = task_service.update_task(
            task_id,
            title=title,
            description=description,
            notes=notes,
            correlation_id=correlation_id,
            status=status,
            priority=priority,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if t is None:
        raise HTTPException(404, "Task not found")
    return _task_out(t)


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int) -> dict:
    if not task_service.delete_task(task_id):
        raise HTTPException(404, "Task not found")
    return {"ok": True, "id": task_id}


@app.get("/api/tasks/{task_id}/runs")
async def get_task_runs(task_id: int) -> List[dict]:
    if task_service.get_task(task_id) is None:
        raise HTTPException(404, "Task not found")
    return run_service.get_runs_for_task(task_id)


# ── Runs ──────────────────────────────────────────────────────────────────────


@app.get("/api/runs")
async def list_runs(project_id: Optional[int] = None) -> List[dict]:
    return run_service.list_recent_runs(project_id=project_id, limit=500)


# ── Manual execution ──────────────────────────────────────────────────────────


@app.post("/api/tasks/{task_id}/complete")
async def complete_task(
    task_id: int,
    body: Any = Body(default=None),
) -> dict:
    output = "manual completion"
    if isinstance(body, dict) and body.get("output") is not None:
        output = str(body["output"])
    elif isinstance(body, str):
        output = body
    elif body is not None:
        output = str(body)

    task = task_service.get_task(task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    if task["status"] not in ("pending", "in_progress"):
        raise HTTPException(
            400,
            f"Task is already terminal ({task['status']!r}). Cannot complete again.",
        )

    pending_run = next(
        (r for r in run_service.get_runs_for_task(task_id) if r["status"] == "pending_input"),
        None,
    )
    if pending_run is not None:
        rid = int(pending_run["id"])
        try:
            updated, _ = run_service.complete_manual_run(rid, str(output))
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        log.info(f"MANUAL COMPLETE (existing run)  task_id={task_id} run_id={rid}")
        return _task_out(updated)

    run = run_service.create_run(task_id, mode="manual")
    rid = int(run["id"])
    run_service.update_run(rid, "running")
    updated = task_service.update_status(task_id, "done")
    run_service.update_run(rid, "success", output=str(output))
    log.info(f"MANUAL COMPLETE (new run)  task_id={task_id} run_id={rid}")
    return _task_out(updated or task)


# ── Backlog ──────────────────────────────────────────────────────────────────


@app.get("/api/projects/{project_id}/backlog")
async def list_project_backlog(project_id: int, status: Optional[str] = None) -> List[dict]:
    if project_service.get_project(project_id) is None:
        raise HTTPException(404, "Project not found")
    return backlog_service.list_by_project(project_id, status=status)


@app.post("/api/projects/{project_id}/backlog")
async def create_backlog_item(project_id: int, body: dict = Body(...)) -> dict:
    if project_service.get_project(project_id) is None:
        raise HTTPException(404, "Project not found")
    try:
        return backlog_service.create(
            project_id,
            str(body.get("title", "")),
            description=body.get("description"),
            submitted_by=str(body.get("submitted_by", "human")),
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


# ── Approvals ─────────────────────────────────────────────────────────────────


@app.get("/api/projects/{project_id}/approvals")
async def list_entity_approvals(entity_type: str, entity_id: int) -> List[dict]:
    return approval_service.list_by_entity(entity_type, entity_id)


@app.post("/api/projects/{project_id}/approvals")
async def record_approval(project_id: int, body: dict = Body(...)) -> dict:
    try:
        return approval_service.record_approval(
            int(body["project_id"]),
            str(body["entity_type"]),
            int(body["entity_id"]),
            str(body["decision"]),
            reason=body.get("reason"),
            approver_role=str(body.get("approver_role", "human_operator")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc


# ── Validations ───────────────────────────────────────────────────────────────


@app.get("/api/projects/{project_id}/validations")
async def list_project_validations(project_id: int) -> List[dict]:
    return validation_service.list_by_project(project_id)


# ── Blueprints ────────────────────────────────────────────────────────────────


@app.get("/api/projects/{project_id}/blueprints")
async def list_blueprints(
    project_id: int,
    blueprint_type: Optional[str] = None,
) -> List[dict]:
    if project_service.get_project(project_id) is None:
        raise HTTPException(404, "Project not found")
    return blueprint_service.list_by_project(
        project_id, blueprint_type=blueprint_type
    )


@app.post("/api/projects/{project_id}/blueprints")
async def create_blueprint(project_id: int, body: dict = Body(...)) -> dict:
    if project_service.get_project(project_id) is None:
        raise HTTPException(404, "Project not found")
    try:
        return blueprint_service.create(
            project_id,
            str(body.get("type", "prd")),
            str(body.get("title", "")),
            str(body.get("content", "")),
            version=int(body.get("version", 1)),
            created_by=body.get("created_by"),
            correlation_id=body.get("correlation_id"),
            write_reason=body.get("write_reason"),
            source_proposal_ref=body.get("source_proposal_ref"),
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/api/blueprints/{blueprint_id}")
async def get_blueprint(blueprint_id: int) -> dict:
    row = blueprint_service.get(blueprint_id)
    if row is None:
        raise HTTPException(404, "Blueprint not found")
    return row


@app.put("/api/blueprints/{blueprint_id}")
async def put_blueprint(blueprint_id: int, body: dict = Body(...)) -> dict:
    row = blueprint_service.update(
        blueprint_id,
        title=body.get("title"),
        content=body.get("content"),
        version=body.get("version"),
    )
    if row is None:
        raise HTTPException(404, "Blueprint not found")
    return row


@app.delete("/api/blueprints/{blueprint_id}")
async def del_blueprint(blueprint_id: int) -> dict:
    if not blueprint_service.delete(blueprint_id):
        raise HTTPException(404, "Blueprint not found")
    return {"ok": True, "id": blueprint_id}


# ── Decisions ─────────────────────────────────────────────────────────────────


@app.get("/api/projects/{project_id}/decisions")
async def list_project_decisions(project_id: int) -> List[dict]:
    if project_service.get_project(project_id) is None:
        raise HTTPException(404, "Project not found")
    return decision_service.list_decisions(project_id=project_id)


@app.post("/api/projects/{project_id}/decisions")
async def create_decision(project_id: int, body: dict = Body(...)) -> dict:
    if project_service.get_project(project_id) is None:
        raise HTTPException(404, "Project not found")
    try:
        return decision_service.add_decision(
            str(body.get("title", "")),
            str(body.get("content", "")),
            project_id=project_id,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


# ── Memory ────────────────────────────────────────────────────────────────────


@app.get("/api/projects/{project_id}/memory")
async def list_project_memory(project_id: int) -> List[dict]:
    if project_service.get_project(project_id) is None:
        raise HTTPException(404, "Project not found")
    return memory_service.list_memory(project_id=project_id)


@app.put("/api/projects/{project_id}/memory/{key:path}")
async def put_memory(project_id: int, key: str, body: dict = Body(...)) -> dict:
    if project_service.get_project(project_id) is None:
        raise HTTPException(404, "Project not found")
    value = body.get("value")
    try:
        return memory_service.upsert_memory(
            project_id, key, str(value) if value is not None else ""
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


# ── Session logs ──────────────────────────────────────────────────────────────


@app.get("/api/projects/{project_id}/session-logs")
async def list_session_logs(project_id: int, limit: int = 100) -> List[dict]:
    if project_service.get_project(project_id) is None:
        raise HTTPException(404, "Project not found")
    return session_log_service.list_by_project(project_id, limit=limit)


@app.post("/api/projects/{project_id}/session-logs")
async def create_session_log(project_id: int, body: dict = Body(...)) -> dict:
    if project_service.get_project(project_id) is None:
        raise HTTPException(404, "Project not found")
    try:
        return session_log_service.create(
            project_id,
            str(body.get("session_date", "")),
            agent=body.get("agent"),
            scope_active=body.get("scope_active"),
            tasks_completed=body.get("tasks_completed"),
            next_task=body.get("next_task"),
            git_state=body.get("git_state"),
            open_issues=body.get("open_issues"),
            notes=body.get("notes"),
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/api/projects/{project_id}/session-logs/latest")
async def latest_session_log(project_id: int) -> dict:
    if project_service.get_project(project_id) is None:
        raise HTTPException(404, "Project not found")
    row = session_log_service.get_latest(project_id)
    if row is None:
        raise HTTPException(404, "No session logs for this project")
    return row


# ── Proposed actions ──────────────────────────────────────────────────────────


@app.get("/api/proposed-actions")
async def list_proposed_actions(project_id: Optional[int] = None) -> List[dict]:
    return proposed_action_service.list_pending(project_id=project_id)


@app.get("/api/proposed-actions/all")
async def list_all_proposed_actions(project_id: Optional[int] = None) -> List[dict]:
    return proposed_action_service.list_all(project_id=project_id)


@app.post("/api/proposed-actions/{action_id}/approve")
async def approve_proposed_action(action_id: int) -> dict:
    try:
        updated = proposed_action_service.approve(action_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"Approval failed: {exc}") from exc
    log.info(f"PROPOSED ACTION APPROVED  id={action_id}")
    return updated


@app.post("/api/proposed-actions/{action_id}/reject")
async def reject_proposed_action(
    action_id: int,
    note: str = Body(default=""),
) -> dict:
    try:
        updated = proposed_action_service.reject(action_id, note=note or None)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    log.info(f"PROPOSED ACTION REJECTED  id={action_id}  note={note!r}")
    return updated


# ── Auxiliary agent outputs ───────────────────────────────────────────────────


@app.get("/api/auxiliary-agent-outputs")
async def list_auxiliary_outputs(project_id: int) -> List[dict]:
    if project_service.get_project(project_id) is None:
        raise HTTPException(404, "Project not found")
    return auxiliary_agent_output_service.list_by_project(project_id)


@app.post("/api/auxiliary-agent-outputs")
async def create_auxiliary_output(body: dict = Body(...)) -> dict:
    try:
        pid = int(body["project_id"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(400, "project_id is required") from None
    if project_service.get_project(pid) is None:
        raise HTTPException(404, "Project not found")
    agent_role = str(body.get("agent_role", "")).strip()
    if not agent_role:
        raise HTTPException(400, "agent_role is required")
    content = str(body.get("content", "")).strip()
    if not content:
        raise HTTPException(400, "content is required")
    related_decision_id = body.get("related_decision_id")
    if related_decision_id is not None:
        try:
            related_decision_id = int(related_decision_id)
        except (TypeError, ValueError):
            raise HTTPException(400, "related_decision_id must be an integer") from None
    row = auxiliary_agent_output_service.create(
        pid,
        agent_role,
        content,
        target_core_agent=body.get("target_core_agent") or None,
        related_requirement_ref=body.get("related_requirement_ref") or None,
        related_decision_id=related_decision_id,
    )
    log.info(f"AUX OUTPUT CREATED  id={row['id']}  project_id={pid}  agent_role={agent_role!r}")
    return row


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("─" * 60)
    log.info("Task Dashboard starting  →  http://localhost:8765")
    log.info(f"Services: {_SERVICES_DIR}")
    log.info("─" * 60)
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8765)), log_level="warning")
