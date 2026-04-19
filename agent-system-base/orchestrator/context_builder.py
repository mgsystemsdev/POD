from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from orchestrator.models import MAX_CONTEXT_BYTES, dump_json, load_json_file


def _join_excerpt(items: list[Any] | None, max_chars: int) -> str:
    if not items:
        return ""
    blob = " | ".join(str(x) for x in items if x)
    if len(blob) <= max_chars:
        return blob
    return blob[: max_chars - 1] + "…"


def build_prior_summaries(run_dir: Path, from_run: list[str], excerpt_chars: int = 1200) -> tuple[list[dict[str, Any]], list[str]]:
    summaries: list[dict[str, Any]] = []
    dependency_paths: list[str] = []
    for fn in from_run:
        p = run_dir / fn
        dependency_paths.append(fn)
        if not p.exists():
            summaries.append({"file": fn, "missing": True})
            continue
        data = load_json_file(p)
        summaries.append(
            {
                "file": fn,
                "agent": data.get("agent"),
                "outputs_excerpt": _join_excerpt(data.get("outputs"), excerpt_chars),
                "decisions_excerpt": _join_excerpt(data.get("decisions"), excerpt_chars),
            }
        )
    return summaries, dependency_paths


def build_context_payload(
    *,
    run_id: str,
    plan_id: str,
    step_id: str,
    goal: str,
    agent_name: str,
    prior_summaries: list[dict[str, Any]],
    dependency_paths: list[str],
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "plan_id": plan_id,
        "step_id": step_id,
        "goal": goal,
        "agent": agent_name,
        "prior_summaries": prior_summaries,
        "dependency_paths": dependency_paths,
        "note": "Full prior JSON lives under run_dir at dependency_paths; keep this file under size cap.",
    }


def enforce_context_size(payload: dict[str, Any], run_dir: Path, max_bytes: int = MAX_CONTEXT_BYTES) -> dict[str, Any]:
    """Shrink prior_summaries excerpts until serialized payload fits max_bytes."""
    payload = dict(payload)
    excerpt = 1200
    for _ in range(24):
        blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        if len(blob.encode("utf-8")) <= max_bytes:
            return payload
        excerpt = max(100, excerpt // 2)
        pr = payload.get("prior_summaries")
        if isinstance(pr, list):
            new_list = []
            for item in pr:
                if not isinstance(item, dict):
                    new_list.append(item)
                    continue
                cp = dict(item)
                for k in ("outputs_excerpt", "decisions_excerpt"):
                    if k in cp and isinstance(cp[k], str) and len(cp[k]) > excerpt:
                        cp[k] = cp[k][: excerpt - 1] + "…"
                new_list.append(cp)
            payload["prior_summaries"] = new_list
        else:
            break

    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if len(blob.encode("utf-8")) <= max_bytes:
        return payload

    rid = payload.get("run_id", "")
    return {
        "run_id": rid,
        "plan_id": payload.get("plan_id"),
        "step_id": payload.get("step_id"),
        "goal": payload.get("goal"),
        "agent": payload.get("agent"),
        "prior_summaries": [],
        "dependency_paths": payload.get("dependency_paths", []),
        "truncated": True,
        "note": f"TRUNCATED: context exceeded {max_bytes} bytes; read full JSON from run_dir {run_dir} paths in dependency_paths.",
    }


def write_context_file(path: Path, payload: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    capped = enforce_context_size(payload, run_dir)
    dump_json(path, capped)
    return capped
