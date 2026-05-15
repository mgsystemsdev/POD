#!/usr/bin/env python3
"""
generate_actions.py — fetch the live POD OpenAPI schema and emit one
per-agent `actions.json` (OpenAPI 3.1) scoped to that agent's allowed
endpoints, ready to paste into a ChatGPT custom-GPT "Actions" editor.

Run:   python3 "MGPOD/Official agents/_tools/generate_actions.py"
Source of truth: https://pod-production-63e3.up.railway.app/openapi.json
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────────
LIVE_OPENAPI_URL = "https://pod-production-63e3.up.railway.app/openapi.json"
SERVER_URL = "https://pod-production-63e3.up.railway.app"
OFFICIAL_AGENTS_ROOT = Path(__file__).resolve().parent.parent  # MGPOD/Official agents/

# Per-agent allowlist. Key = relative folder under OFFICIAL_AGENTS_ROOT.
# Value = list of (path, method) pairs allowed for that agent.
# `method` is uppercase HTTP verb. Paths must match the live schema exactly.
AGENT_SCOPE: dict[str, list[tuple[str, str]]] = {
    # ── Core pipeline ──────────────────────────────────────────────────────
    "core/architect": [
        ("/api/projects", "GET"),
        ("/api/projects", "POST"),                           # create project
        ("/api/projects/{project_id}", "PUT"),               # rename/update project
        ("/api/projects/{project_id}/blueprints", "GET"),
        ("/api/projects/{project_id}/blueprints", "POST"),
        ("/api/blueprints/{blueprint_id}", "GET"),
        ("/api/blueprints/{blueprint_id}", "PUT"),
        ("/api/blueprints/{blueprint_id}", "DELETE"),        # clean up stale blueprints
        ("/api/projects/{project_id}/decisions", "GET"),
        ("/api/projects/{project_id}/decisions", "POST"),
        ("/api/projects/{project_id}/memory", "GET"),
        ("/api/projects/{project_id}/memory/{key}", "PUT"),
    ],
    "core/execution-spec-gate": [
        ("/api/projects", "GET"),
        ("/api/projects/{project_id}/blueprints", "GET"),
        ("/api/blueprints/{blueprint_id}", "GET"),
        ("/api/projects/{project_id}/decisions", "GET"),
        ("/api/tasks", "POST"),
    ],
    "core/strategist": [
        ("/api/projects", "GET"),
        ("/api/projects/{project_id}/blueprints", "GET"),
        ("/api/projects/{project_id}/decisions", "GET"),
        ("/api/auxiliary-agent-outputs", "GET"),
        ("/api/auxiliary-agent-outputs", "POST"),
    ],
    "core/operator": [
        ("/api/projects", "GET"),
        ("/api/tasks", "GET"),
        ("/api/tasks/{task_id}", "GET"),
        ("/api/tasks/{task_id}", "PUT"),
        ("/api/tasks/{task_id}/complete", "POST"),
        ("/api/tasks/{task_id}/runs", "GET"),
        ("/api/runs", "GET"),
        ("/api/projects/{project_id}/blueprints", "GET"),
        ("/api/blueprints/{blueprint_id}", "GET"),
        ("/api/projects/{project_id}/decisions", "GET"),
        ("/api/projects/{project_id}/memory", "GET"),
        ("/api/projects/{project_id}/memory/{key}", "PUT"),
        ("/api/proposed-actions", "GET"),
        ("/api/proposed-actions/{action_id}/approve", "POST"),
        ("/api/proposed-actions/{action_id}/reject", "POST"),
        ("/api/projects/{project_id}/session-logs", "GET"),
        ("/api/projects/{project_id}/session-logs", "POST"),
        ("/api/projects/{project_id}/session-logs/latest", "GET"),
    ],
    # blueprint-creator: intentionally skipped (draft-only, no DB writes)

    # ── Auxiliary specialists (advisory only → write proposals) ────────────
    **{
        f"auxiliary/{a}": [
            ("/api/projects", "GET"),
            ("/api/projects/{project_id}/blueprints", "GET"),
            ("/api/blueprints/{blueprint_id}", "GET"),
            ("/api/projects/{project_id}/decisions", "GET"),
            ("/api/auxiliary-agent-outputs", "GET"),
            ("/api/auxiliary-agent-outputs", "POST"),
        ]
        for a in (
            "senior_dev",
            "database_specialist",
            "schema_specialist",
            "backend_specialist",
            "ui_specialist",
            "system_design",
        )
    },
}

# ── Backend dependency ─────────────────────────────────────────────────────────
# DELETE /api/projects/{project_id}: NOT in live API as of 2026-04-19.
# Until added: Architect uses soft-delete (PUT name → "[ARCHIVED] {name}").
# When backend adds it: add ("/api/projects/{project_id}", "DELETE") to
# AGENT_SCOPE["core/architect"] and regenerate actions.json.

# Nice descriptive title per agent (used in info.title/description).
AGENT_META: dict[str, dict[str, str]] = {
    "core/architect": {
        "title": "Architect Actions (POD)",
        "role": "Project Lifecycle Manager + Requirements Authority. Creates and manages projects in the registry. Produces canonical project.md (Section A + B) and schema.json. Reads/writes projects, blueprints, decisions, memory.",
    },
    "core/execution-spec-gate": {
        "title": "Execution Spec Gate Actions (POD)",
        "role": "Translates validated Section B into execution-safe tasks.json. Reads projects/blueprints/decisions; writes tasks.",
    },
    "core/strategist": {
        "title": "Auxiliary Strategist Actions (POD)",
        "role": "Advisory design-thinking partner. Reads projects/blueprints/decisions; writes proposals via auxiliary-agent-outputs.",
    },
    "core/operator": {
        "title": "Operator Actions (POD)",
        "role": "Executes dashboard tasks. Reads/updates tasks, reads runs/decisions/memory/blueprints/proposed-actions, approves/rejects proposed actions, writes session logs.",
    },
    "auxiliary/senior_dev": {
        "title": "Senior Dev Actions (POD)",
        "role": "Advisory senior-engineering specialist. Reads projects/blueprints/decisions; writes proposals via auxiliary-agent-outputs.",
    },
    "auxiliary/database_specialist": {
        "title": "Database Specialist Actions (POD)",
        "role": "Advisory database specialist. Reads projects/blueprints/decisions; writes proposals via auxiliary-agent-outputs.",
    },
    "auxiliary/schema_specialist": {
        "title": "Schema Specialist Actions (POD)",
        "role": "Advisory schema specialist. Reads projects/blueprints/decisions; writes proposals via auxiliary-agent-outputs.",
    },
    "auxiliary/backend_specialist": {
        "title": "Backend Specialist Actions (POD)",
        "role": "Advisory backend specialist. Reads projects/blueprints/decisions; writes proposals via auxiliary-agent-outputs.",
    },
    "auxiliary/ui_specialist": {
        "title": "UI Specialist Actions (POD)",
        "role": "Advisory UI specialist. Reads projects/blueprints/decisions; writes proposals via auxiliary-agent-outputs.",
    },
    "auxiliary/system_design": {
        "title": "System Design Actions (POD)",
        "role": "Advisory system-design specialist. Reads projects/blueprints/decisions; writes proposals via auxiliary-agent-outputs.",
    },
}


# ── Helpers ────────────────────────────────────────────────────────────────────
def fetch_live_schema(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def agent_slug(relpath: str) -> str:
    return relpath.replace("/", "_").replace("-", "_")


# Known request-body shapes inferred from agent-system-base/system/dashboard/server.py.
# Keyed by (path, METHOD). Replaces the empty object body that FastAPI emits for
# endpoints declared as `body: dict = Body(...)`.
KNOWN_BODY_SCHEMAS: dict[tuple[str, str], dict] = {
    ("/api/projects", "POST"): {
        "type": "object",
        "required": ["name", "slug"],
        "properties": {
            "name": {"type": "string"},
            "slug": {"type": "string"},
            "root_path": {"type": ["string", "null"]},
            "upsert": {"type": "boolean", "default": False},
        },
        "additionalProperties": False,
    },
    ("/api/projects/{project_id}", "PUT"): {
        "type": "object",
        "properties": {
            "name": {"type": ["string", "null"]},
            "root_path": {"type": ["string", "null"]},
        },
        "additionalProperties": False,
    },
    ("/api/tasks", "POST"): {
        "type": "object",
        "required": ["project_id", "title"],
        "properties": {
            "project_id": {"type": "integer"},
            "title": {"type": "string"},
            "description": {"type": ["string", "null"]},
            "priority": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "description": "1=urgent, 2=high, 3=normal, 4=low, 5=low",
            },
            "notes": {"type": ["string", "null"]},
            "correlation_id": {"type": ["string", "null"]},
            "requirement_ref": {"type": ["string", "null"]},
            "decision_id": {"type": ["integer", "null"]},
        },
        "additionalProperties": False,
    },
    ("/api/tasks/{task_id}", "PUT"): {
        "type": "object",
        "properties": {
            "title": {"type": ["string", "null"]},
            "description": {"type": ["string", "null"]},
            "notes": {"type": ["string", "null"]},
            "correlation_id": {"type": ["string", "null"]},
            "status": {
                "type": ["string", "null"],
                "enum": ["pending", "in_progress", "done", "blocked", "cancelled", None],
            },
            "priority": {"type": ["integer", "null"], "minimum": 1, "maximum": 5},
        },
        "additionalProperties": False,
    },
    ("/api/tasks/{task_id}/complete", "POST"): {
        "type": "object",
        "properties": {
            "output": {"type": "string", "description": "Completion note / output text"},
        },
        "additionalProperties": False,
    },
    ("/api/projects/{project_id}/blueprints", "POST"): {
        "type": "object",
        "required": ["title", "content"],
        "properties": {
            "type": {"type": "string", "default": "prd"},
            "title": {"type": "string"},
            "content": {"type": "string"},
            "version": {"type": "integer", "default": 1},
        },
        "additionalProperties": False,
    },
    ("/api/blueprints/{blueprint_id}", "PUT"): {
        "type": "object",
        "properties": {
            "title": {"type": ["string", "null"]},
            "content": {"type": ["string", "null"]},
            "version": {"type": ["integer", "null"]},
        },
        "additionalProperties": False,
    },
    ("/api/projects/{project_id}/decisions", "POST"): {
        "type": "object",
        "required": ["title", "content"],
        "properties": {
            "title": {"type": "string"},
            "content": {"type": "string"},
        },
        "additionalProperties": False,
    },
    ("/api/projects/{project_id}/memory/{key}", "PUT"): {
        "type": "object",
        "required": ["value"],
        "properties": {
            "value": {"type": "string"},
        },
        "additionalProperties": False,
    },
    ("/api/projects/{project_id}/session-logs", "POST"): {
        "type": "object",
        "required": ["session_date"],
        "properties": {
            "session_date": {"type": "string", "description": "ISO date YYYY-MM-DD"},
            "agent": {"type": ["string", "null"]},
            "scope_active": {"type": ["string", "null"]},
            "tasks_completed": {"type": ["string", "null"]},
            "next_task": {"type": ["string", "null"]},
            "git_state": {"type": ["string", "null"]},
            "open_issues": {"type": ["string", "null"]},
            "notes": {"type": ["string", "null"]},
        },
        "additionalProperties": False,
    },
    ("/api/proposed-actions/{action_id}/reject", "POST"): {
        "type": "string",
        "description": "Optional rejection note",
    },
    ("/api/auxiliary-agent-outputs", "POST"): {
        "type": "object",
        "required": ["project_id", "agent_role", "content"],
        "properties": {
            "project_id": {"type": "integer"},
            "agent_role": {
                "type": "string",
                "description": "e.g. senior_dev, database_specialist, schema_specialist, backend_specialist, ui_specialist, system_design, strategist",
            },
            "content": {"type": "string"},
            "target_core_agent": {
                "type": ["string", "null"],
                "description": "Which core agent this advice is for, if any",
            },
            "related_requirement_ref": {"type": ["string", "null"]},
            "related_decision_id": {"type": ["integer", "null"]},
        },
        "additionalProperties": False,
    },
}


def _inject_known_body(op: dict, path: str, method: str) -> None:
    """If a known body schema exists for (path, method), overwrite the requestBody schema."""
    key = (path, method.upper())
    if key not in KNOWN_BODY_SCHEMAS:
        return
    body = op.setdefault("requestBody", {"required": True, "content": {}})
    body.setdefault("content", {}).setdefault("application/json", {})["schema"] = KNOWN_BODY_SCHEMAS[key]


def _patch_bare_objects(node):
    """
    Recursively walk the schema tree and fix any object schemas that lack
    `properties`. ChatGPT Actions validator rejects `{type: object}` without
    an explicit `properties` key, even when `additionalProperties: true` is set.

    Also replaces a completely empty JSON Schema ``{}`` (e.g. FastAPI default
    response model) with an explicit object shape — strict clients reject bare
    ``{}``.
    """
    if isinstance(node, dict):
        s = node.get("schema")
        if isinstance(s, dict) and len(s) == 0:
            node["schema"] = {
                "type": "object",
                "properties": {},
                "additionalProperties": True,
            }
        if node.get("type") == "object" and "properties" not in node:
            node["properties"] = {}
            node.setdefault("additionalProperties", True)
        for v in node.values():
            _patch_bare_objects(v)
    elif isinstance(node, list):
        for v in node:
            _patch_bare_objects(v)


def build_agent_schema(source: dict, relpath: str, scope: list[tuple[str, str]]) -> dict:
    meta = AGENT_META[relpath]
    source_paths = source.get("paths", {})
    filtered_paths: dict = {}

    for path, method in scope:
        method_lc = method.lower()
        if path not in source_paths or method_lc not in source_paths[path]:
            raise KeyError(f"{relpath}: {method} {path} not in live schema")

        op = json.loads(json.dumps(source_paths[path][method_lc]))
        op["operationId"] = f"{agent_slug(relpath)}__{method_lc}_{path_key(path)}"
        op["security"] = [{"ApiKeyAuth": []}]
        _inject_known_body(op, path, method)

        filtered_paths.setdefault(path, {})[method_lc] = op

    schema = {
        "openapi": "3.1.0",
        "info": {
            "title": meta["title"],
            "version": source["info"].get("version", "1.0.0"),
            "description": meta["role"],
        },
        "servers": [{"url": SERVER_URL, "description": "POD on Railway (production)"}],
        "paths": filtered_paths,
        "components": {
            **source.get("components", {}),
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "Dashboard API key. Configure in ChatGPT Actions \u2192 Authentication \u2192 API Key \u2192 Custom header X-API-Key.",
                }
            },
        },
        "security": [{"ApiKeyAuth": []}],
    }
    _patch_bare_objects(schema)
    return schema


def path_key(path: str) -> str:
    return (
        path.replace("/api/", "")
        .replace("/", "_")
        .replace("{", "")
        .replace("}", "")
        .replace("-", "_")
        .strip("_")
    )


# ── Entry point ────────────────────────────────────────────────────────────────
def main() -> int:
    print(f"Fetching live OpenAPI from {LIVE_OPENAPI_URL} ...")
    source = fetch_live_schema(LIVE_OPENAPI_URL)
    print(f"  openapi={source.get('openapi')}  paths={len(source.get('paths', {}))}")

    if not OFFICIAL_AGENTS_ROOT.is_dir():
        print(f"ERROR: expected dir {OFFICIAL_AGENTS_ROOT}", file=sys.stderr)
        return 2

    written = 0
    for relpath, scope in AGENT_SCOPE.items():
        agent_dir = OFFICIAL_AGENTS_ROOT / relpath
        if not agent_dir.is_dir():
            print(f"  SKIP (missing dir): {relpath}")
            continue
        schema = build_agent_schema(source, relpath, scope)
        payload = json.dumps(schema, indent=2) + "\n"
        out = agent_dir / "actions.json"
        out.write_text(payload, encoding="utf-8")
        ops = sum(len(m) for m in schema["paths"].values())
        print(f"  wrote {out.relative_to(OFFICIAL_AGENTS_ROOT.parent)}  ops={ops}  bytes={out.stat().st_size}")
        if relpath == "core/architect":
            bundle_out = agent_dir / "agent-architecture-official" / "actions.json"
            if bundle_out.parent.is_dir():
                bundle_out.write_text(payload, encoding="utf-8")
                print(f"  also {bundle_out.relative_to(OFFICIAL_AGENTS_ROOT.parent)}  (GPT bundle)")
        written += 1

    print(f"\nDone. {written} files written under {OFFICIAL_AGENTS_ROOT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
