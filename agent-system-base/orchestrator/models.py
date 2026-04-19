from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "2"
MAX_CONTEXT_BYTES = 10240

REQUIRED_KEYS: tuple[str, ...] = (
    "agent",
    "goal",
    "inputs",
    "actions",
    "outputs",
    "decisions",
    "artifacts",
    "next_steps",
)


@dataclass
class ValidationError(Exception):
    message: str
    path: str = ""

    def __str__(self) -> str:
        return f"{self.path}: {self.message}" if self.path else self.message


def normalize_goal(s: str) -> str:
    return " ".join(s.strip().split())


def iso_timestamp_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def input_hash_v2(
    context_payload: Mapping[str, Any],
    agent_def: Mapping[str, Any],
) -> str:
    raw = canonical_json(
        {
            "context_for": context_payload,
            "agent_def": agent_def,
            "schema_version": SCHEMA_VERSION,
        }
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def validate_agent_output(obj: Any, path: str = "$") -> dict[str, Any]:
    """Validate mandatory agent output envelope (v1 shape; arrays of strings)."""
    if not isinstance(obj, dict):
        raise ValidationError("root must be an object", path)
    for key in REQUIRED_KEYS:
        if key not in obj:
            raise ValidationError(f"missing required key {key!r}", path)
    if not isinstance(obj["agent"], str) or not obj["agent"].strip():
        raise ValidationError("agent must be non-empty string", f"{path}.agent")
    if not isinstance(obj["goal"], str):
        raise ValidationError("goal must be a string", f"{path}.goal")
    for arr_name in ("inputs", "actions", "outputs", "decisions", "artifacts", "next_steps"):
        if not isinstance(obj[arr_name], list):
            raise ValidationError(f"{arr_name} must be an array", f"{path}.{arr_name}")
        for i, item in enumerate(obj[arr_name]):
            if not isinstance(item, str):
                raise ValidationError(f"{arr_name}[{i}] must be a string", f"{path}.{arr_name}[{i}]")
    if "meta" in obj and obj["meta"] is not None and not isinstance(obj["meta"], dict):
        raise ValidationError("meta must be an object if present", f"{path}.meta")
    return obj  # type: ignore[return-value]


_ISO_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
)


def _validate_iso_timestamp(ts: str, path: str) -> None:
    if not isinstance(ts, str) or not _ISO_RE.match(ts.strip()):
        raise ValidationError("meta.timestamp must be ISO-8601 UTC string", path)


def validate_agent_output_v2(
    obj: Any,
    *,
    expected_agent: str,
    expected_goal: str,
    run_id: str,
    step_id: str,
    path: str = "$",
) -> dict[str, Any]:
    """Strict v2 envelope + per-agent extensions on success."""
    o = validate_agent_output(obj, path)
    if "status" not in o:
        raise ValidationError("missing required key 'status'", path)
    if o["status"] not in ("success", "failure"):
        raise ValidationError("status must be 'success' or 'failure'", f"{path}.status")

    meta = o.get("meta")
    if not isinstance(meta, dict):
        raise ValidationError("meta must be an object", f"{path}.meta")
    for mk in ("run_id", "step_id", "schema_version", "agent", "timestamp"):
        if mk not in meta:
            raise ValidationError(f"meta missing required key {mk!r}", f"{path}.meta")
    if meta["run_id"] != run_id:
        raise ValidationError("meta.run_id mismatch", f"{path}.meta.run_id")
    if meta["step_id"] != step_id:
        raise ValidationError("meta.step_id mismatch", f"{path}.meta.step_id")
    if meta["schema_version"] != SCHEMA_VERSION:
        raise ValidationError(f"unsupported meta.schema_version (expected {SCHEMA_VERSION!r})", path)
    if meta["agent"] != o["agent"] or meta["agent"] != expected_agent:
        raise ValidationError("meta.agent must match top-level agent and plan step", f"{path}.meta.agent")
    _validate_iso_timestamp(str(meta["timestamp"]), f"{path}.meta.timestamp")

    ng = normalize_goal(o["goal"])
    eg = normalize_goal(expected_goal)
    if ng != eg:
        raise ValidationError("goal mismatch vs run goal", f"{path}.goal")

    if o["status"] == "failure":
        if not o["decisions"] or not any(str(d).strip() for d in o["decisions"]):
            raise ValidationError("failure status requires non-empty decisions", f"{path}.decisions")
        return o

    # success path — per-agent requirements
    agent = expected_agent
    if agent == "research":
        sc = o.get("sources_checked")
        if not isinstance(sc, list) or not sc or not all(isinstance(x, str) and x.strip() for x in sc):
            raise ValidationError(
                "research agent requires non-empty sources_checked: string[]", f"{path}.sources_checked"
            )
    elif agent == "context":
        du = o.get("docs_used")
        if not isinstance(du, list) or not du or not all(isinstance(x, str) and x.strip() for x in du):
            raise ValidationError("context agent requires non-empty docs_used: string[]", f"{path}.docs_used")
    elif agent == "create":
        if not o["artifacts"] or not all(a.strip() for a in o["artifacts"]):
            raise ValidationError("create agent requires non-empty artifacts on success", f"{path}.artifacts")

    return o


def validate_merged_output(
    obj: Any,
    *,
    expected_goal: str,
    run_id: str,
    step_id: str,
    path: str = "$",
) -> dict[str, Any]:
    """merged.json: v2 merge agent envelope + conflicts array."""
    o = validate_agent_output_v2(
        obj,
        expected_agent="merge",
        expected_goal=expected_goal,
        run_id=run_id,
        step_id=step_id,
        path=path,
    )
    if "conflicts" not in o:
        raise ValidationError("merged output requires 'conflicts' array", path)
    c = o["conflicts"]
    if not isinstance(c, list):
        raise ValidationError("conflicts must be an array", f"{path}.conflicts")
    for i, item in enumerate(c):
        if not isinstance(item, dict):
            raise ValidationError(f"conflicts[{i}] must be an object", path)
        for k in ("type", "agents", "reason", "resolution"):
            if k not in item:
                raise ValidationError(f"conflicts[{i}] missing {k!r}", path)
        if not isinstance(item["agents"], list) or not all(isinstance(a, str) for a in item["agents"]):
            raise ValidationError(f"conflicts[{i}].agents must be string array", path)
    return o


def load_json_file(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def fingerprint(goal: str, agent: str, prior_keys: Sequence[str]) -> str:
    raw = json.dumps({"agent": agent, "goal": goal, "prior": list(prior_keys)}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def validate_with_retry_v2(
    raw: Any,
    *,
    expected_agent: str,
    expected_goal: str,
    run_id: str,
    step_id: str,
    retries: int = 1,
) -> dict[str, Any]:
    last: ValidationError | None = None
    for _ in range(retries + 1):
        try:
            return validate_agent_output_v2(
                raw,
                expected_agent=expected_agent,
                expected_goal=expected_goal,
                run_id=run_id,
                step_id=step_id,
            )
        except ValidationError as e:
            last = e
    assert last is not None
    raise last


def failure_envelope_v2(
    agent: str,
    goal: str,
    err: str,
    *,
    run_id: str,
    step_id: str,
) -> dict[str, Any]:
    return {
        "agent": agent,
        "goal": goal,
        "status": "failure",
        "inputs": [],
        "actions": [],
        "outputs": [],
        "decisions": [f"ERROR: {err}"],
        "artifacts": [],
        "next_steps": ["Inspect logs and fix API or validation errors."],
        "meta": {
            "run_id": run_id,
            "step_id": step_id,
            "schema_version": SCHEMA_VERSION,
            "agent": agent,
            "timestamp": iso_timestamp_now(),
        },
    }


def simulate_envelope_v2(
    agent_name: str,
    goal: str,
    tool_meta: dict[str, Any],
    prior_summary: str,
    *,
    run_id: str,
    step_id: str,
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "agent": agent_name,
        "goal": goal,
        "status": "success",
        "inputs": [prior_summary[:4000] + ("…" if len(prior_summary) > 4000 else "")],
        "actions": ["orchestrator:simulate", "tools:assessed"],
        "outputs": [
            f"Simulated pass for {agent_name}. Replace with API execute mode for real output."
        ],
        "decisions": [str(x) for x in tool_meta.get("fallback_notes", [])][:8],
        "artifacts": [],
        "next_steps": [f"Validate {agent_name}.output.json against schemas/agent_output_v2.schema.json"],
        "meta": {
            "run_id": run_id,
            "step_id": step_id,
            "schema_version": SCHEMA_VERSION,
            "agent": agent_name,
            "timestamp": iso_timestamp_now(),
        },
    }
    if agent_name == "research":
        base["sources_checked"] = ["orchestrator/simulated"]
    elif agent_name == "context":
        base["docs_used"] = ["CLAUDE.md", "AGENTS.md", "claude-system/orchestrator/README.md"]
    elif agent_name == "create":
        base["artifacts"] = [f"claude-system/runs/ephemeral/{run_id}/.simulated_create_marker"]
    base["meta"]["tool_strategy"] = tool_meta
    return base
