from __future__ import annotations

import json
import time
import traceback
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from orchestrator.context_builder import build_context_payload, build_prior_summaries, write_context_file
from orchestrator.merge import merge_agent_outputs
from orchestrator.models import (
    SCHEMA_VERSION,
    ValidationError,
    dump_json,
    failure_envelope_v2,
    fingerprint,
    input_hash_v2,
    iso_timestamp_now,
    load_json_file,
    simulate_envelope_v2,
    validate_agent_output_v2,
    validate_with_retry_v2,
)
from orchestrator.runner.api import AnthropicApiRunner
from orchestrator.tool_validation import resolve_tool_strategy


class OrchestratorAbort(Exception):
    """Critical step failed; downstream work must not run."""


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_agent(name: str, root: Path | None = None) -> dict[str, Any]:
    p = (root or repo_root()) / "agents" / f"{name}.json"
    if not p.exists():
        raise FileNotFoundError(f"agent definition not found: {p}")
    return load_json_file(p)


def load_plan(plan_id: str, root: Path | None = None) -> dict[str, Any]:
    p = (root or repo_root()) / "agents" / "plans" / f"{plan_id}.json"
    if not p.exists():
        raise FileNotFoundError(f"plan not found: {p}")
    return load_json_file(p)


def topological_waves(steps: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    done: set[str] = set()
    waves: list[list[dict[str, Any]]] = []
    total = len(steps)
    while len(done) < total:
        ready = [
            s
            for s in steps
            if s["step_id"] not in done and all(d in done for d in s.get("depends_on", []))
        ]
        if not ready:
            raise ValueError("Invalid plan: cycle or unknown depends_on")
        for s in ready:
            done.add(s["step_id"])
        waves.append(ready)
    return waves


def output_filename_for_step(step: dict[str, Any]) -> str:
    return step.get("output_file", f"{step['agent']}.output.json")


def template_str(s: str, run_id: str, goal: str) -> str:
    return s.replace("{{run_id}}", run_id).replace("{goal}", goal)


def is_critical(agent_def: dict[str, Any], step: dict[str, Any]) -> bool:
    return bool(agent_def.get("critical"))


@dataclass
class RunConfig:
    plan_id: str
    goal: str
    mode: str  # simulate | handoff | execute
    reuse_outputs: bool
    run_id: str | None = None


class Orchestrator:
    def __init__(self, runs_dir: Path | None = None) -> None:
        self.root = repo_root()
        self.runs_dir = runs_dir or (self.root / "runs" / "ephemeral")
        self.registry_path = self.runs_dir / "registry.json"

    def _load_registry(self) -> dict[str, Any]:
        if not self.registry_path.exists():
            return {"fingerprints": {}}
        return load_json_file(self.registry_path)

    def _save_registry(self, reg: dict[str, Any]) -> None:
        dump_json(self.registry_path, reg)

    def _init_run_state(self, run_id: str, cfg: RunConfig, waves_len: int) -> dict[str, Any]:
        now = iso_timestamp_now()
        return {
            "run_id": run_id,
            "plan_id": cfg.plan_id,
            "goal": cfg.goal,
            "mode": cfg.mode,
            "schema_version": SCHEMA_VERSION,
            "created_at": now,
            "steps_completed": [],
            "errors": [],
            "next_wave": 0,
            "total_waves": waves_len,
            "reuse_outputs": cfg.reuse_outputs,
            "run": {
                "started_at": now,
                "finished_at": None,
                "total_duration_ms": None,
                "status": "running",
            },
            "steps": {},
        }

    def _step_touch(
        self,
        state: dict[str, Any],
        step_id: str,
        *,
        status: str | None = None,
        duration_ms: int | None = None,
        retries: int | None = None,
        input_hash: str | None = None,
        token_usage: dict[str, int] | None = None,
    ) -> None:
        st = state.setdefault("steps", {}).setdefault(step_id, {})
        if status is not None:
            st["status"] = status
        if duration_ms is not None:
            st["duration_ms"] = duration_ms
        if retries is not None:
            st["retries"] = retries
        if input_hash is not None:
            st["input_hash"] = input_hash
        if token_usage is not None:
            st["token_usage"] = token_usage

    def execute(self, cfg: RunConfig) -> Path:
        plan = load_plan(cfg.plan_id, self.root)
        steps: list[dict[str, Any]] = plan["steps"]
        run_id = cfg.run_id or str(uuid.uuid4())
        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        effective_goal = template_str(cfg.goal, run_id, cfg.goal)
        waves = topological_waves(steps)
        state_path = run_dir / "run_state.json"
        state = self._init_run_state(run_id, cfg, len(waves))
        state["goal"] = effective_goal
        state["goal_template"] = cfg.goal
        dump_json(state_path, state)

        reg = self._load_registry()
        t_run0 = time.perf_counter()

        try:
            if cfg.mode == "handoff":
                self._run_wave(
                    waves[0],
                    plan=plan,
                    cfg=cfg,
                    run_dir=run_dir,
                    run_id=run_id,
                    state=state,
                    state_path=state_path,
                    reg=reg,
                    effective_goal=effective_goal,
                )
                state["next_wave"] = 1
            else:
                for i, wave in enumerate(waves):
                    if state.get("run", {}).get("status") == "failed":
                        break
                    self._run_wave(
                        wave,
                        plan=plan,
                        cfg=cfg,
                        run_dir=run_dir,
                        run_id=run_id,
                        state=state,
                        state_path=state_path,
                        reg=reg,
                        effective_goal=effective_goal,
                    )
                    state["next_wave"] = i + 1
                    dump_json(state_path, state)
        except OrchestratorAbort:
            state.setdefault("run", {})["status"] = "failed"
            dump_json(state_path, state)

        total_ms = int((time.perf_counter() - t_run0) * 1000)
        state.setdefault("run", {})
        if state["run"].get("status") != "failed":
            if cfg.mode == "handoff" and int(state.get("next_wave", 0)) < int(state.get("total_waves", 0)):
                state["run"]["status"] = "paused"
            else:
                state["run"]["status"] = "completed"
        state["run"]["finished_at"] = iso_timestamp_now()
        state["run"]["total_duration_ms"] = total_ms
        dump_json(state_path, state)
        self._save_registry(reg)
        return run_dir

    def _run_wave(
        self,
        wave: list[dict[str, Any]],
        *,
        plan: dict[str, Any],
        cfg: RunConfig,
        run_dir: Path,
        run_id: str,
        state: dict[str, Any],
        state_path: Path,
        reg: dict[str, Any],
        effective_goal: str,
    ) -> None:
        if state.get("run", {}).get("status") == "failed":
            return
        parallel_groups: dict[int | str, list[dict[str, Any]]] = {}
        for step in wave:
            pg = step.get("parallel_group", 0)
            parallel_groups.setdefault(pg, []).append(step)
        state.setdefault("wave_log", []).append(
            {
                "parallel_groups": {str(k): [s["step_id"] for s in v] for k, v in parallel_groups.items()},
            }
        )
        for step in wave:
            if state.get("run", {}).get("status") == "failed":
                break
            self._run_step(
                step=step,
                plan=plan,
                cfg=cfg,
                run_dir=run_dir,
                run_id=run_id,
                state=state,
                state_path=state_path,
                reg=reg,
                effective_goal=effective_goal,
            )

    def _run_step(
        self,
        *,
        step: dict[str, Any],
        plan: dict[str, Any],
        cfg: RunConfig,
        run_dir: Path,
        run_id: str,
        state: dict[str, Any],
        state_path: Path,
        reg: dict[str, Any],
        effective_goal: str,
        log: Callable[[str], None] | None = None,
    ) -> None:
        log = log or (lambda m: None)
        step_id = step["step_id"]
        agent_name = step["agent"]
        out_name = output_filename_for_step(step)
        out_path = run_dir / out_name

        if step.get("builtin_merge"):
            t0 = time.perf_counter()
            self._step_touch(state, step_id, status="running")
            dump_json(state_path, state)
            try:
                self._builtin_merge_step(step, effective_goal, run_dir, out_path, state, state_path, run_id)
            except OrchestratorAbort:
                ms = int((time.perf_counter() - t0) * 1000)
                self._step_touch(state, step_id, status="failure", duration_ms=ms)
                dump_json(state_path, state)
                raise
            except Exception:
                ms = int((time.perf_counter() - t0) * 1000)
                self._step_touch(state, step_id, status="failure", duration_ms=ms)
                dump_json(state_path, state)
                raise
            ms = int((time.perf_counter() - t0) * 1000)
            self._step_touch(state, step_id, status="success", duration_ms=ms, retries=0)
            state["steps_completed"].append(step_id)
            dump_json(state_path, state)
            return

        agent_def = load_agent(agent_name, self.root)
        from_run = step.get("inputs", {}).get("from_run", [])
        prior_summaries, dep_paths = build_prior_summaries(run_dir, from_run)

        context_payload = build_context_payload(
            run_id=run_id,
            plan_id=plan["plan_id"],
            step_id=step_id,
            goal=effective_goal,
            agent_name=agent_name,
            prior_summaries=prior_summaries,
            dependency_paths=dep_paths,
        )
        context_path = run_dir / f"context_for_{agent_name}.json"
        capped_payload = write_context_file(context_path, context_payload, run_dir)
        input_hash = input_hash_v2(capped_payload, agent_def)

        strategy = resolve_tool_strategy(
            list(agent_def.get("tools_preferred", [])),
            list(agent_def.get("tools_fallback", [])),
        )
        fp = fingerprint(effective_goal, agent_name, sorted(dep_paths))
        fingerprints: dict[str, Any] = reg.setdefault("fingerprints", {})

        prev_hash = state.get("steps", {}).get(step_id, {}).get("input_hash")
        if cfg.reuse_outputs and out_path.exists() and prev_hash == input_hash:
            try:
                validate_with_retry_v2(
                    load_json_file(out_path),
                    expected_agent=agent_name,
                    expected_goal=effective_goal,
                    run_id=run_id,
                    step_id=step_id,
                )
                log(f"reuse valid output: {out_path.name}")
                state["steps_completed"].append(step_id)
                self._step_touch(state, step_id, status="success", input_hash=input_hash, duration_ms=0, retries=0)
                fingerprints.setdefault(fp, {"run_id": run_id, "step_id": step_id})
                dump_json(state_path, state)
                return
            except ValidationError:
                log(f"stale output invalid, regenerating: {out_path.name}")

        if cfg.mode == "handoff":
            handoff = {
                "instruction": (
                    f"Read {context_path.name}; run skill '{agent_def.get('skill', agent_name)}'; "
                    f"write {out_name} matching schemas/agent_output_v2.schema.json (status, meta.run_id, meta.step_id, …)."
                ),
                "tool_strategy": strategy,
                "required_file": out_name,
                "schema_version": SCHEMA_VERSION,
            }
            dump_json(run_dir / f"HANDOFF_{step_id}.json", handoff)
            state.setdefault("handoff_pending", []).append(step_id)
            self._step_touch(state, step_id, status="pending_handoff", input_hash=input_hash)
            dump_json(state_path, state)
            return

        t0 = time.perf_counter()
        self._step_touch(state, step_id, status="running", input_hash=input_hash)
        dump_json(state_path, state)

        retries = 0
        token_usage = {"input": 0, "output": 0}

        def handle_failure(err: str) -> None:
            nonlocal retries
            fe = failure_envelope_v2(agent_name, effective_goal, err, run_id=run_id, step_id=step_id)
            dump_json(out_path, fe)
            ms = int((time.perf_counter() - t0) * 1000)
            self._step_touch(
                state,
                step_id,
                status="failure",
                duration_ms=ms,
                retries=retries,
                token_usage=dict(token_usage),
            )
            state["errors"].append({"step_id": step_id, "error": err})
            state["steps_completed"].append(step_id)
            fingerprints[fp] = {"run_id": run_id, "step_id": step_id}
            dump_json(state_path, state)
            if is_critical(agent_def, step):
                state.setdefault("run", {})["status"] = "failed"
                state["abort_reason"] = f"critical step {step_id} failed: {err}"
                dump_json(state_path, state)
                raise OrchestratorAbort(state["abort_reason"])

        try:
            if cfg.mode == "execute":
                log_path = run_dir / "logs" / f"{step_id}_{agent_name}_1.txt"
                runner = AnthropicApiRunner()
                for attempt in range(2):
                    retries = attempt
                    log_path = run_dir / "logs" / f"{step_id}_{agent_name}_{attempt + 1}.txt"
                    res = runner.run_step(context_path=context_path, agent_name=agent_name, log_path=log_path)
                    token_usage["input"] += res.token_usage.get("input", 0)
                    token_usage["output"] += res.token_usage.get("output", 0)
                    if res.parsed is None:
                        if attempt == 1:
                            handle_failure(res.error or "runner returned no JSON")
                            return
                        continue
                    try:
                        validate_agent_output_v2(
                            res.parsed,
                            expected_agent=agent_name,
                            expected_goal=effective_goal,
                            run_id=run_id,
                            step_id=step_id,
                        )
                        dump_json(out_path, res.parsed)
                        break
                    except ValidationError as ve:
                        if attempt == 1:
                            handle_failure(str(ve))
                            return
                else:
                    handle_failure("exhausted retries")
                    return
            else:
                summary_blob = json.dumps(capped_payload, ensure_ascii=False)
                body = simulate_envelope_v2(
                    agent_name,
                    effective_goal,
                    strategy,
                    summary_blob,
                    run_id=run_id,
                    step_id=step_id,
                )
                retries = 0
                try:
                    validate_agent_output_v2(
                        body,
                        expected_agent=agent_name,
                        expected_goal=effective_goal,
                        run_id=run_id,
                        step_id=step_id,
                    )
                    dump_json(out_path, body)
                except ValidationError as ve:
                    handle_failure(f"simulate envelope validation failed: {ve}")
                    return

            raw = load_json_file(out_path)
            if raw.get("status") == "failure":
                handle_failure("; ".join(raw.get("decisions") or []) or "agent reported failure")
                return

            ms = int((time.perf_counter() - t0) * 1000)
            self._step_touch(
                state,
                step_id,
                status="success",
                duration_ms=ms,
                retries=retries,
                input_hash=input_hash,
                token_usage=dict(token_usage),
            )
            fingerprints[fp] = {"run_id": run_id, "step_id": step_id}
            state["steps_completed"].append(step_id)
            dump_json(state_path, state)
        except OrchestratorAbort:
            raise
        except Exception as e:
            traceback.print_exc()
            handle_failure(f"{e!s}")

    def _builtin_merge_step(
        self,
        step: dict[str, Any],
        goal: str,
        run_dir: Path,
        merged_path: Path,
        state: dict[str, Any],
        state_path: Path,
        run_id: str,
    ) -> None:
        from_run = step.get("inputs", {}).get("from_run", [])
        merge_step_id = step["step_id"]
        retries = 0

        def attempt() -> None:
            merge_agent_outputs(
                goal=goal,
                run_dir=run_dir,
                source_filenames=from_run,
                merged_path=merged_path,
                run_id=run_id,
                merge_step_id=merge_step_id,
            )

        try:
            attempt()
        except Exception as e1:
            retries = 1
            state["errors"].append({"step_id": merge_step_id, "attempt": 1, "error": str(e1)})
            try:
                attempt()
            except Exception as e2:
                state["errors"].append({"step_id": merge_step_id, "attempt": 2, "error": str(e2)})
                fe = failure_envelope_v2("merge", goal, str(e2), run_id=run_id, step_id=merge_step_id)
                fe["conflicts"] = []
                dump_json(merged_path, fe)
                if is_critical(load_agent("merge", self.root), step):
                    state.setdefault("run", {})["status"] = "failed"
                    state["abort_reason"] = f"merge failed: {e2}"
                    dump_json(state_path, state)
                    raise OrchestratorAbort(state["abort_reason"]) from e2
        dump_json(state_path, state)

    def resume_handoff_advance(self, run_id: str) -> Path:
        run_dir = self.runs_dir / run_id
        if not run_dir.is_dir():
            raise FileNotFoundError(run_dir)
        state_path = run_dir / "run_state.json"
        state = load_json_file(state_path)
        if state.get("mode") != "handoff":
            raise ValueError("resume_handoff_advance only applies to mode=handoff runs")
        plan = load_plan(state["plan_id"], self.root)
        waves = topological_waves(plan["steps"])
        nw = int(state["next_wave"])
        if nw >= len(waves):
            return run_dir

        effective_goal = state["goal"]
        rid = state["run_id"]

        if nw > 0:
            for st in waves[nw - 1]:
                if st.get("builtin_merge"):
                    continue
                out_path = run_dir / output_filename_for_step(st)
                if not out_path.exists():
                    raise FileNotFoundError(f"Advance blocked; missing {out_path.name}")
                validate_with_retry_v2(
                    load_json_file(out_path),
                    expected_agent=st["agent"],
                    expected_goal=effective_goal,
                    run_id=rid,
                    step_id=st["step_id"],
                )

        reg = self._load_registry()
        cfg = RunConfig(
            plan_id=state["plan_id"],
            goal=state.get("goal_template") or state["goal"],
            mode="handoff",
            reuse_outputs=bool(state.get("reuse_outputs", False)),
        )
        self._run_wave(
            waves[nw],
            plan=plan,
            cfg=cfg,
            run_dir=run_dir,
            run_id=rid,
            state=state,
            state_path=state_path,
            reg=reg,
            effective_goal=effective_goal,
        )
        state["next_wave"] = nw + 1
        dump_json(state_path, state)
        self._save_registry(reg)
        return run_dir

    def resume_handoff_finish(self, run_id: str) -> Path:
        run_dir = self.runs_dir / run_id
        state_path = run_dir / "run_state.json"
        state = load_json_file(state_path)
        plan = load_plan(state["plan_id"], self.root)
        steps: list[dict[str, Any]] = plan["steps"]
        effective_goal = state["goal"]
        rid = state["run_id"]
        for st in steps:
            if st.get("builtin_merge"):
                continue
            out_path = run_dir / output_filename_for_step(st)
            if not out_path.exists():
                raise FileNotFoundError(f"Missing handoff output: {out_path}")
            validate_with_retry_v2(
                load_json_file(out_path),
                expected_agent=st["agent"],
                expected_goal=effective_goal,
                run_id=rid,
                step_id=st["step_id"],
            )
        for st in steps:
            if st.get("builtin_merge"):
                merged_path = run_dir / output_filename_for_step(st)
                self._builtin_merge_step(st, effective_goal, run_dir, merged_path, state, state_path, rid)
        state["next_wave"] = len(topological_waves(steps))
        state["handoff_pending"] = []
        dump_json(state_path, state)
        return run_dir
