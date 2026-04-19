from __future__ import annotations

import difflib
import json
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

from orchestrator.models import (
    SCHEMA_VERSION,
    dump_json,
    iso_timestamp_now,
    load_json_file,
    validate_agent_output_v2,
    validate_merged_output,
)


SIMILARITY_THRESHOLD = 0.3
MIN_OUTPUT_LEN_FOR_DIVERGENCE = 80


def _norm_artifact_path(s: str) -> str:
    s = s.strip().replace("\\", "/")
    while "//" in s:
        s = s.replace("//", "/")
    try:
        return str(PurePosixPath(s))
    except ValueError:
        return s


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def detect_conflicts(pieces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    agents = [p["agent"] for p in pieces]

    # Rule 1: artifact collision
    path_to_agents: dict[str, list[str]] = defaultdict(list)
    for p in pieces:
        if p.get("status") != "success":
            continue
        for art in p.get("artifacts") or []:
            if not isinstance(art, str) or not art.strip():
                continue
            norm = _norm_artifact_path(art)
            path_to_agents[norm].append(p["agent"])
    for path, ags in path_to_agents.items():
        uniq = sorted(set(ags))
        if len(uniq) > 1:
            conflicts.append(
                {
                    "type": "artifact_collision",
                    "agents": uniq,
                    "reason": f"Same artifact path claimed by multiple agents: {path}",
                    "resolution": None,
                }
            )

    # Rule 2: decision tension (pairwise agents, joined decisions)
    succ = [p for p in pieces if p.get("status") == "success"]
    for i, a in enumerate(succ):
        for b in succ[i + 1 :]:
            da = " | ".join(a.get("decisions") or [])
            db = " | ".join(b.get("decisions") or [])
            if len(da.strip()) < 3 or len(db.strip()) < 3:
                continue
            if _similarity(da, db) < SIMILARITY_THRESHOLD:
                conflicts.append(
                    {
                        "type": "decision_tension",
                        "agents": sorted({a["agent"], b["agent"]}),
                        "reason": (
                            f"Low similarity ({_similarity(da, db):.2f}) between decisions of "
                            f"{a['agent']} vs {b['agent']}"
                        ),
                        "resolution": None,
                    }
                )

    # Rule 3: output divergence
    for i, a in enumerate(succ):
        for b in succ[i + 1 :]:
            oa = " ".join(a.get("outputs") or [])
            ob = " ".join(b.get("outputs") or [])
            if len(oa) < MIN_OUTPUT_LEN_FOR_DIVERGENCE or len(ob) < MIN_OUTPUT_LEN_FOR_DIVERGENCE:
                continue
            if _similarity(oa, ob) < SIMILARITY_THRESHOLD:
                conflicts.append(
                    {
                        "type": "output_divergence",
                        "agents": sorted({a["agent"], b["agent"]}),
                        "reason": (
                            f"Low similarity ({_similarity(oa, ob):.2f}) between outputs of "
                            f"{a['agent']} vs {b['agent']}"
                        ),
                        "resolution": None,
                    }
                )

    return conflicts


def merge_agent_outputs(
    *,
    goal: str,
    run_dir: Path,
    source_filenames: list[str],
    merged_path: Path,
    run_id: str,
    merge_step_id: str,
) -> dict[str, Any]:
    """Load validated v2 per-agent outputs; detect conflicts; write merged.json (v2 + conflicts)."""
    pieces: list[dict[str, Any]] = []
    for name in source_filenames:
        p = run_dir / name
        if not p.exists():
            raise FileNotFoundError(f"missing merge input: {p}")
        raw = load_json_file(p)
        meta = raw.get("meta") or {}
        rid = str(meta.get("run_id", run_id))
        sid = str(meta.get("step_id", ""))
        if not sid:
            raise ValueError(f"missing step_id in {name}")
        pieces.append(
            validate_agent_output_v2(
                raw,
                expected_agent=str(raw.get("agent", "")),
                expected_goal=goal,
                run_id=rid,
                step_id=sid,
                path=str(p),
            )
        )

    conflicts = detect_conflicts(pieces)

    merged: dict[str, Any] = {
        "agent": "merge",
        "goal": goal,
        "status": "success",
        "inputs": [f"merged from: {', '.join(source_filenames)}"],
        "actions": ["orchestrator.merge.merge_agent_outputs"],
        "outputs": [],
        "decisions": [],
        "artifacts": [merged_path.name],
        "next_steps": [],
        "conflicts": conflicts,
        "meta": {
            "run_id": run_id,
            "step_id": merge_step_id,
            "schema_version": SCHEMA_VERSION,
            "agent": "merge",
            "timestamp": iso_timestamp_now(),
            "sources": source_filenames,
            "piece_agents": [p["agent"] for p in pieces],
        },
    }

    if conflicts:
        merged["next_steps"].append("Review conflicts[] and set resolution fields after human triage.")

    for p in pieces:
        merged["outputs"].append(f"[{p['agent']}] " + "; ".join(p["outputs"][:3]))
        if len(p["outputs"]) > 3:
            merged["outputs"].append(f"[{p['agent']}] ... +{len(p['outputs']) - 3} more output lines")
        merged["decisions"].extend(f"[{p['agent']}] {d}" for d in p["decisions"])
        merged["next_steps"].extend(f"[{p['agent']}] {n}" for n in p["next_steps"])

    def dedupe(seq: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    merged["outputs"] = dedupe(merged["outputs"])
    merged["decisions"] = dedupe(merged["decisions"])
    merged["next_steps"] = dedupe(merged["next_steps"])

    validate_merged_output(
        merged,
        expected_goal=goal,
        run_id=run_id,
        step_id=merge_step_id,
        path="merged",
    )
    dump_json(merged_path, merged)

    # Emit any tasks_to_create from agent outputs to the global task board
    emitted = _emit_tasks(pieces)
    if emitted:
        merged["meta"]["tasks_emitted"] = emitted

    return merged


_GLOBAL_TASKS = Path.home() / ".claude" / "tasks.json"


def _emit_tasks(pieces: list[dict[str, Any]]) -> int:
    """Append any tasks_to_create from agent outputs to ~/.claude/tasks.json.

    Returns the number of tasks written.
    """
    new_tasks: list[dict[str, Any]] = []
    for p in pieces:
        for task in p.get("tasks_to_create") or []:
            if isinstance(task, dict) and task.get("task_id"):
                new_tasks.append(task)

    if not new_tasks:
        return 0

    existing: list[dict[str, Any]] = []
    if _GLOBAL_TASKS.exists():
        try:
            existing = json.loads(_GLOBAL_TASKS.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except (json.JSONDecodeError, OSError):
            existing = []

    existing_ids = {t.get("task_id") for t in existing}
    to_add = [t for t in new_tasks if t.get("task_id") not in existing_ids]

    if to_add:
        _GLOBAL_TASKS.parent.mkdir(parents=True, exist_ok=True)
        _GLOBAL_TASKS.write_text(
            json.dumps(existing + to_add, indent=2) + "\n", encoding="utf-8"
        )

    return len(to_add)


def load_outputs_map(run_dir: Path, filenames: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for fn in filenames:
        p = run_dir / fn
        if p.exists():
            out[fn] = load_json_file(p)
    return out
