# SYSTEM AUDIT — agent-system-base

> **Snapshot notice:** Point-in-time audit from **2026-03-23**. Re-verify claims against the current blueprint repo and `init.sh` before operational use (see [`README.md`](../../README.md)).

**Date:** 2026-03-23
**Auditor:** Claude Code — Principal Systems Auditor

---

## 1. Executive Summary

This system is currently **multiple competing systems sharing files**, not one unified execution system.

What is proven:
- There are three competing task contracts in active code:
  - Dashboard contract (`id`, no `action_type`) in `system/dashboard/server.py:63-73`
  - Worker contract (`task_id`, `action_type`, `action_payload`) in `workers/task_worker.py:318-365` and `config/task_schema.json:7-26`
  - Legacy ad-hoc tasks in live `~/.claude/tasks.json` where 85/87 tasks have no `action_type` (measured by command output).
- The dashboard is wired to `~/.claude/tasks.json` (`system/dashboard/server.py:24`) but rewrites tasks using `Task.model_dump()` (`system/dashboard/server.py:88`), which drops worker fields (`task_id`, `action_type`, `action_payload`, `correlation_id`).
- Dashboard IDs are non-stable for existing tasks lacking `id`; `_load()` rehydrates with generated UUIDs each request (`system/dashboard/server.py:63-64,79-84`). I reproduced this: two loads yield different IDs and update fails with 404.
- The worker and orchestrator deployment are drifted from blueprint:
  - Base worker supports `run_plan` and env gating (`agent-system-base/workers/task_worker.py:45-47,230-271`), deployed worker does not (`~/agent-services/workers/task_worker.py:6-11,214-219`).
  - Base orchestrator merge emits `tasks_to_create` (`orchestrator/merge.py:197-240`), deployed `~/.claude/orchestrator/merge.py` does not.
  - Base runner injects SKILL.md content in execute mode (`orchestrator/runner/api.py:20-47,97,104`), deployed runner does not (`~/.claude/orchestrator/runner/api.py:18-29,62-69`).
- Automation is not active: `crontab -l` returns `NO_CRONTAB`, dashboard port 8765 unused, and no worker/orchestrator processes found.

Top risk conclusion:
- The control plane (dashboard) can corrupt the execution contract for automation by rewriting `tasks.json` into a shape the worker cannot execute reliably.
- The execution plane (worker/orchestrator) is partially deployed and drifted, so documented behavior and actual runtime behavior diverge.
- System classification: **Needs stabilization first**.

## 2. System Inventory

### 2.1 Runtime-Relevant Directories and Components

1. Blueprint repo: `/Users/miguelgonzalez/agent-system-base`
- What it is: source-of-truth editing repo (`CLAUDE.md:3-16`).
- What depends on it: `init.sh` deployment to `~/.claude` and `~/agent-services` (`init.sh:9-23`).
- What it depends on: rsync, path assumptions, existing target paths.
- Used at runtime: **indirectly** only after sync.
- Source of truth status: **declared source-of-truth**, but drift exists.

2. Global Claude runtime: `~/.claude`
- What it is: live orchestrator/agents/skills/tasks state (`~/.claude` listing).
- What depends on it:
  - Worker reads/writes `~/.claude/tasks.json` (`workers/task_worker.py:43,387-393`).
  - Dashboard reads/writes same file (`system/dashboard/server.py:24,79-89`).
  - Orchestrator execute worker path (from worker `run_plan`) assumes `cwd=~/.claude` (`workers/task_worker.py:249` in blueprint).
- Used at runtime: **yes (direct)**.
- Source of truth status: **actual runtime truth**, but not synchronized with blueprint.

3. Runtime services layer: `~/agent-services`
- What it is: deployed workers/dashboard/config/cron installer.
- What depends on it:
  - Cron entries point here (`~/agent-services/install.sh:14-18`).
  - Logs/state paths in deployed worker (`~/agent-services/workers/task_worker.py:36-41`).
- Used at runtime: intended direct runtime; currently inactive (no crontab).

4. Dashboard API/UI
- Blueprint: `system/dashboard/server.py`, `system/dashboard/index.html`.
- Deployed: `~/agent-services/system/dashboard/*`.
- What it does: CRUD against `~/.claude/tasks.json` with FastAPI.
- Dependents: human operators.
- Enforced/optional: optional (manual start).
- Production relevance: **production-relevant but currently inactive**.

5. Worker
- Blueprint: `workers/task_worker.py`.
- Deployed: `~/agent-services/workers/task_worker.py` (older variant).
- What it does: polls global and per-project task boards, dispatches actions.
- Dependents: cron/manual invocations.
- Production relevance: **core execution engine but inactive and drifted**.

6. Orchestrator
- Blueprint: `orchestrator/*`.
- Deployed: `~/.claude/orchestrator/*` (drifted in critical files).
- What it does: DAG execution (`orchestrator/controller.py:151-215`), schema validation (`orchestrator/models.py:94-227`), merge (`orchestrator/merge.py`).
- Dependents: `run_plan` worker action (blueprint only) and manual CLI.
- Production relevance: core engine, but partially disconnected from current worker deployment.

7. Agent/plan definitions
- `agents/*.json`, `agents/plans/*.json`.
- What they do: define plan DAG and tool preferences.
- Dependents: orchestrator loader (`orchestrator/controller.py:38-49,152-153`).
- Runtime usage:
  - In blueprint orchestration: yes.
  - In deployed runtime: only whichever files were synced into `~/.claude/agents`.

8. Skills
- `./.claude/skills/*/SKILL.md` and deployed `~/.claude/skills/*/SKILL.md`.
- What they do: intended instruction payload for agents.
- Runtime usage:
  - Blueprint runner in execute mode: yes (`orchestrator/runner/api.py:20-47,62-64,97`).
  - Deployed runner: **no skill injection** (`~/.claude/orchestrator/runner/api.py:18-29`).
- Status: **illusion of completeness** in deployed runtime.

9. Schemas
- `schemas/agent_output.schema.json`, `schemas/agent_output_v2.schema.json`, `config/task_schema.json`.
- Runtime enforcement:
  - Agent output v2: enforced by Python validators, not JSON schema files (`orchestrator/models.py:94-227`).
  - Task schema: **not enforced anywhere** (no jsonschema call sites).

10. Automation scripts
- `workers/install.sh`, `system/scripts/start_dashboard.sh`, `system/scripts/check_decisions.py`, `workers/decision_reviewer.py`, `workers/gmail_triage.py`.
- Runtime usage:
  - Cron installer exists, but no crontab installed.
  - `gmail_triage.py` exits at auth TODO (`workers/gmail_triage.py:49-60`): scaffolding.
  - `system/scripts/check_decisions.py` has no runtime call path from installer: decorative/dead for current automation.

### 2.2 Dead Code / Decorative / Scaffolding / Broken Wiring

1. `workers/gmail_triage.py`
- Label: **scaffolding**.
- Evidence: explicit TODO status and hard `sys.exit(1)` in `authenticate()` (`workers/gmail_triage.py:11-13,49-60`).

2. `system/scripts/check_decisions.py`
- Label: **dead code** in current automation path.
- Evidence: cron installer uses `workers/decision_reviewer.py` (`workers/install.sh:16`), not this script.

3. `workers/review.sh`
- Label: **decorative/manual utility**.
- Evidence: no call sites from worker/orchestrator/dashboard.

4. `orchestrator` parallel groups
- Label: **illusion of completeness**.
- Evidence: groups are logged (`orchestrator/controller.py:232-240`) but execution is sequential loop over `wave` (`orchestrator/controller.py:241-255`). No parallel execution primitives.

5. Registry fingerprints
- Label: **partial wiring/decorative**.
- Evidence: fingerprints written (`orchestrator/controller.py:320,335,379,458`) but never consulted to skip/cross-run dedupe.

6. Task schema files
- Label: **illusion of enforcement**.
- Evidence: schemas exist (`config/task_schema.json`) but worker/dashboard do not validate input against them.

7. Deployed worker `run_plan` capability
- Label: **broken wiring vs blueprint**.
- Evidence: base supports `run_plan` (`agent-system-base/workers/task_worker.py:230-271`), deployed worker lacks it (`~/agent-services/workers/task_worker.py:214-219`).

## 3. True Execution Graph

### 3.1 Actual Entrypoints (Proven)

1. Orchestrator CLI
- Entry: `python3 -m orchestrator` → `orchestrator/__main__.py:1-4` → `orchestrator/run_cli.py:10-90`.

2. Dashboard server
- Entry: `python3 system/dashboard/server.py` → FastAPI app (`system/dashboard/server.py:96-180`).

3. Worker
- Entry: `python workers/task_worker.py` (`workers/task_worker.py:375-428` blueprint; deployed variant `:320-371`).

4. Cron installation
- Entry: `bash install.sh` in runtime layer (`~/agent-services/install.sh:1-37`), not active.

### 3.2 Real End-to-End Paths

1. Dashboard path (current behavior)
- User opens UI (`index.html`) and calls `/api/tasks`.
- Server `_load()` parses `~/.claude/tasks.json` into `Task` model (`server.py:79-84`).
- Because most tasks have `task_id` but no `id` (measured: 87/87 missing `id`), `id` is generated on each load (`Task.id` default factory, `server.py:63-64`).
- UI sends update/delete by transient `id`; next request re-loads with different IDs; update/delete misses and returns 404 (`update_task`/`delete_task`, `server.py:121-149`). I reproduced this with direct function call.
- If save eventually happens, `_save()` writes only dashboard model keys (`server.py:88`), dropping worker contract fields.

2. Worker path (current deployed runtime)
- Worker loads tasks from `~/.claude/tasks.json` and project tasks (`~/agent-services/workers/task_worker.py:330-359`).
- For each pending task, if `action_type` missing, defaults to `log_only` (`:225`).
- `log_only` requires `action_payload.message` (`:134-138`), absent in most legacy tasks.
- Task becomes `blocked` (`:237-240,287-309`).
- Since 34 pending global tasks have no `action_type`, those are effectively non-executable with current worker.

3. Orchestrator path (blueprint)
- `RunConfig` loaded from CLI (`run_cli.py:68-74`).
- Plan loaded from `agents/plans/*.json` (`controller.py:45-49,152-153`).
- Steps executed wave by wave with per-step context files (`controller.py:217-255,302-313`).
- In simulate mode, synthetic envelope emitted (`controller.py:420-441` via `simulate_envelope_v2`).
- Merge executed with builtin merge function (`controller.py:467-509`).

4. Orchestrator path (deployed runtime)
- Uses `~/.claude/orchestrator/*`.
- Missing base features due drift:
  - No `_emit_tasks` in merge.
  - No SKILL.md injection in API runner.

### 3.3 Major Flow Variants

1. Happy path (theoretical, blueprint)
- Valid task schema + executable `action_type` + active cron/worker + orchestrator with synced runtime.
- Not currently realized due inactive cron and malformed pending tasks.

2. Common failure path
- Pending task without `action_type` → defaults `log_only` → blocked (`task_worker.py:225,134-138,237`).
- Silent accumulation of blocked tasks if dashboard cannot represent blocked status.

3. Silent failure path
- Dashboard rewrites `tasks.json` without worker fields, no warning (`server.py:88`).
- Operator sees task board but automation metadata is erased.

4. Partial success path
- Orchestrator simulate produces valid envelopes and merged output (`runs/ephemeral/...`).
- But emitted tasks integration exists only in blueprint, not deployed runtime.

5. Duplicate execution path risk
- No global lock or idempotency token on task dispatch; state-based dedupe only by `processed_tasks` map, which is independent of task status.

6. Loop/runaway path risk
- If task is retriggered with new `task_id` and no guardrails, worker will execute again; no semantic dedupe beyond ID.

7. Stale-state path
- `processed_tasks` prevents rerun of same `task_id` even if task reset to pending manually (design in `already_processed`, `record_result`).

### 3.4 Files Read/Written by Core Flows

1. Dashboard
- Reads/writes: `~/.claude/tasks.json`.
- Logs: `~/agent-services/logs/dashboard.log` (blueprint/deployed runtime variant).

2. Worker
- Reads: `~/.claude/tasks.json`, per-project `tasks.json`, `~/agent-services/config/projects_index.json`.
- Writes: those task files, `~/agent-services/state/task_worker_state.json`, worker log.

3. Orchestrator
- Reads: `agents/*.json`, `agents/plans/*.json`, prior outputs.
- Writes: run directory outputs, `run_state.json`, `registry.json`, optional logs.
- Base merge writes to `~/.claude/tasks.json` via `_emit_tasks`; deployed merge does not.

## 4. Hidden Assumptions

1. Tasks always include executable action contract.
- Assumed by worker dispatch.
- Violated in live data (34 pending tasks missing `action_type`).

2. Dashboard and worker schemas are compatible.
- False. Dashboard model omits worker-required fields and has different ID semantics.

3. Task IDs are stable across dashboard requests.
- False for tasks lacking stored `id`; IDs regenerated per load.

4. Status vocabularies align.
- False. Worker includes `blocked` (`config/task_schema.json:15`), dashboard enum excludes it (`server.py:42-46`).

5. Plans marked parallel actually run in parallel.
- False. Execution is sequential.

6. Skill instructions are applied in execute mode.
- True in blueprint runner; false in deployed runner.

7. Merge emits tasks_to_create in runtime.
- True in blueprint; false in deployed runtime.

8. Deployment sync keeps runtime aligned.
- False; proven drift across `workers/task_worker.py`, `orchestrator/merge.py`, `orchestrator/runner/api.py`, and skills/plans inventory.

9. Cron automation exists once installer exists.
- False; no crontab installed.

10. .env carries required credentials.
- False in runtime `.env` (comments only).

## 5. System Invariants

1. Invariant: One task file must preserve execution metadata end-to-end.
- Why: automation requires `action_type` + `action_payload`.
- Enforced: **not enforced**.
- Evidence: dashboard save path drops fields (`server.py:88`).
- Status: **assumed only**.
- Failure: tasks become non-executable.

2. Invariant: Task identity must be stable across read/update/delete.
- Why: UI and worker mutation consistency.
- Enforced: **not enforced** for legacy tasks.
- Evidence: default UUID factory with missing source IDs (`server.py:63-64,79-84`).
- Failure: 404 on updates/deletes and inability to complete tasks.

3. Invariant: Status enums must be shared by dashboard and worker.
- Enforced: **not enforced**.
- Evidence: dashboard lacks `blocked`; worker uses it.
- Failure: parse failures or blind spots.

4. Invariant: Agent output schema v2 must be validated before downstream use.
- Enforced: yes in orchestrator validators (`models.py:94-227`, `controller.py:403-409,431-437,534-540,579-585`).
- Caveat: JSON schema files are not runtime enforcement source.

5. Invariant: Runtime deployment and blueprint must be in sync.
- Enforced: **not enforced**.
- Evidence: diffs across critical files and missing runtime features.

6. Invariant: Automation should be schedulable and active if system claims autonomous behavior.
- Enforced: **optional/manual**, currently inactive (`NO_CRONTAB`).

7. Invariant: Worker should have deterministic retry/idempotency controls.
- Enforced: weak/partial.
- Evidence: no retries, only processed-task map, no lock across processes.

8. Invariant: Orchestrator “parallel_group” semantics should reflect actual concurrency behavior.
- Enforced: **not enforced** (logged only).

## 6. Layer-by-Layer Maturity Assessment

### L1 Context Rules — Score: 4/10

What is real:
- Rich rules/docs in `AGENTS.md`, `CLAUDE.md`, skill files.

Why not higher:
- Major contract drift between docs and runtime behavior.
- Example: AGENTS output example shape differs from actual v2 validator expectations (`AGENTS.md:30-47` vs `models.py:94-152`).
- Docs claim dependency statuses include skipped/completed semantics not implemented as such in run engine.

Real vs implied:
- Real: textual guidance.
- Implied/fake-complete: assumed enforcement in runtime.

### L2 Skills — Score: 5/10

What is real:
- Skill catalog exists and is extensive.
- Agent-skill links mostly present.

Why not higher:
- Deployed orchestrator execute path does not inject skill body (`~/.claude/orchestrator/runner/api.py`).
- Drifted skill files between blueprint and runtime (`intent_router` diff).
- `swarm` skill exists in blueprint but absent in deployed `~/.claude/skills` while merge agent references it.

Real vs implied:
- Real: skill files exist.
- Implied/fake-complete: skills driving execute-mode behavior in deployed runtime.

### L3 Dynamic Hooks — Score: 3/10

What is real:
- Worker dispatch has action handlers and safe path checks.
- Orchestrator can run simulate/handoff/execute.

Why not higher:
- No shared validated task schema enforcement.
- Deployed worker lacks `run_plan`; hook from tasks to orchestrator is broken.
- Dashboard-to-worker hook corrupts contract.

### L4 End-to-End Orchestration — Score: 3/10

What is real:
- Orchestrator core (blueprint) validates outputs and merges.
- One simulate run artifact exists and is coherent.

Why not higher:
- Runtime drift: deployed orchestrator missing merge task emission and skill injection.
- No active scheduler; no running worker/dashboard processes.
- “Parallel” orchestration not truly parallel.

### L5 Hardening / Reliability / Control — Score: 2/10

What is real:
- Some validation and path confinement in worker.
- Structured run state in orchestrator.

Why not higher:
- No end-to-end audit IDs across dashboard→worker→orchestrator.
- No task file locking; race risk.
- No retries/backoff in worker actions.
- No rollback/undo for task mutations.
- No active observability pipeline; logs absent in runtime directories.

## 7. Failure Modes and Breakpoints

1. Dashboard rewrites task board and strips execution metadata
- Trigger: any dashboard task save/update/delete/complete.
- Observed effect: `task_id/action_type/action_payload` lost.
- Hidden effect: worker can no longer execute these tasks.
- Severity: Critical.
- Detectability: Delayed/silent until worker run.
- Containment: none.
- Current mitigation: none.
- Missing mitigation: schema-preserving serializer and compatibility layer.
- Recommended fix: dashboard must round-trip full task object, not `Task.model_dump()` subset.

2. Dashboard cannot stably mutate legacy tasks
- Trigger: attempting edit/complete/delete on tasks without persisted `id`.
- Observed effect: 404 Task not found.
- Hidden effect: operator thinks dashboard is control plane; mutations fail.
- Severity: High.
- Detectability: Visible.
- Mitigation: none.
- Recommended fix: canonical ID mapping (`task_id` as primary key).

3. Worker blocks pending tasks lacking `action_type`
- Trigger: run worker on current global/project task boards.
- Observed effect: default `log_only` then blocked due missing message.
- Hidden effect: backlog stuck while appearing pending.
- Severity: Critical.
- Detectability: Visible in logs only (not active now).
- Mitigation: none.
- Recommended fix: strict validation pre-ingest + migration of legacy tasks.

4. Deployed worker lacks `run_plan`
- Trigger: tasks with `action_type=run_plan` in future.
- Effect: blocked unknown action type.
- Severity: High.
- Detectability: Visible.
- Mitigation: none.
- Recommended fix: sync deployed worker and schema from blueprint.

5. Orchestrator runtime drift drops `tasks_to_create` emission
- Trigger: merge in deployed `~/.claude/orchestrator/merge.py`.
- Effect: generated tasks never land in global board.
- Hidden effect: false impression that merge emits tasks.
- Severity: High.
- Detectability: Silent unless inspected.
- Recommended fix: sync `merge.py` and add contract test.

6. Skills not injected in deployed execute mode
- Trigger: execute mode in deployed runner.
- Effect: generic prompt only; skill behavior absent.
- Severity: High.
- Detectability: Silent quality drift.
- Recommended fix: sync runner API and add execute-mode integration test.

7. No automation active
- Trigger: expecting cron-driven operations.
- Effect: nothing runs.
- Severity: High operationally.
- Detectability: Delayed.
- Recommended fix: install/verify crontab or supervised service.

8. Parallel-group is non-parallel
- Trigger: plans expecting concurrency.
- Effect: sequential execution and scale limits.
- Severity: Medium.
- Detectability: Silent unless timing audited.
- Recommended fix: true parallel executor or rename semantics to avoid deception.

9. Task board concurrent write race
- Trigger: dashboard and worker write same file near-simultaneously.
- Effect: lost updates, clobbered fields.
- Severity: High.
- Detectability: Delayed.
- Mitigation: none.
- Recommended fix: file lock + transactional writes + version checks.

10. Gmail automation presented but non-functional
- Trigger: running gmail worker.
- Effect: exits immediately.
- Hidden effect: “automation exists” illusion.
- Severity: Medium.
- Detectability: Visible.
- Recommended fix: mark disabled in dashboard/control plane; gate cron enablement on auth check.

11. Deployed/blueprint split of dashboard storage targets
- Trigger: running dashboard from different roots (`~/.claude/system/dashboard/server.py` vs `~/agent-services/system/dashboard/server.py`).
- Effect: one points to repo-root `tasks.json`, another to global `~/.claude/tasks.json`.
- Severity: High.
- Detectability: Silent data drift.
- Recommended fix: single storage contract and one canonical deployment target.

12. Validation script gives false confidence
- Trigger: running `validate.sh`.
- Effect: PASS even when runtime is drifted and schemas incompatible.
- Severity: Medium.
- Detectability: Silent.
- Recommended fix: add runtime diff checks and execution-contract tests.

## 8. Control / Safety / Reliability Audit

### 8.1 Observability

Current:
- Orchestrator has run_state and step metrics (`run_state.json`, `controller.py:105-149`).
- Worker/dashboard log to local files.

Gaps:
- No unified trace ID from dashboard action to worker execution to orchestrator run.
- No centralized log ingestion or alerting.
- No runtime logs present in `~/agent-services/logs` right now.

### 8.2 Traceability

Current:
- Worker stores `processed_tasks` in state map.
- Orchestrator stores `run_id` and step IDs.

Gaps:
- Dashboard does not preserve worker task identifiers.
- Correlation ID support exists only in blueprint worker and is absent in deployed worker.

### 8.3 Rollback / Undo

Current:
- None for task mutations.
- Dashboard delete is destructive.

Risk:
- File-based board can be overwritten with lossy format and no revert path.

### 8.4 Retries / Idempotency

Current:
- Orchestrator step retries exist.
- Worker action retries absent.

Gaps:
- Worker idempotency keyed only by historical `task_id`; can prevent legitimate reruns.
- No dedupe for semantic duplicates.

### 8.5 Approval Gates

Current:
- Some skills instruct approval checkpoints (docs only).
- No enforced approval gate in worker/orchestrator for high-impact actions.

### 8.6 Cost / Rate Control

Current:
- Orchestrator tracks token usage per step.

Gaps:
- No budget cap, no rate limit controls, no kill switch from dashboard.

### 8.7 Write Permissions / Blast Radius

Current:
- Worker `safe_path` guards run_script/generate_file paths relative to project.

Gaps:
- `claude_execute` can perform broad actions via prompt with no sandbox policy gating from worker.
- Dashboard directly mutates shared global task board with no schema guards.

### 8.8 Reproducibility / Testability

Current:
- Simulate mode is deterministic-ish for structure.
- `validate.sh` static checks exist.

Gaps:
- No automated integration tests for dashboard-worker compatibility.
- No deployment drift detection in CI.

### 8.9 Source-of-Truth Drift

Proven drift vectors:
- Blueprint vs deployed worker behavior.
- Blueprint vs deployed orchestrator behavior.
- Blueprint vs deployed skills and plans inventory.
- Multiple dashboard server variants with different task file targets.

## 9. Execution Readiness

What is ready now:
1. Blueprint orchestrator simulate/handoff core flow in repo is functional.
2. Agent output v2 validation logic is robust.
3. Merge conflict heuristics are implemented.

What is not ready now:
1. Unified dashboard→worker execution contract.
2. Active automation scheduling.
3. Drift-free deployment baseline.
4. Reliable task execution from current live task board data.

Blocked by hidden dependencies:
1. Correct deployment sync from blueprint to runtime paths.
2. Task schema migration for existing task records.
3. Credential provisioning for execute pathways.

Can be trusted:
1. Orchestrator schema validation functions (`models.py`).
2. Safe-path confinement for script/file actions in worker.

Cannot yet be trusted:
1. Dashboard as control plane for executable tasks.
2. Worker autonomy on current pending task inventory.
3. Docs claiming automation cadence (no crontab).

Requires human review before automation:
1. Any task file migration touching `~/.claude/tasks.json`.
2. Deployment sync operation across `~/.claude` and `~/agent-services`.
3. Enabling cron/autonomous execution.

Safe to automate now:
1. Read-only audits and schema checks.
2. Orchestrator simulate runs in isolated run directories.

Should not be automated yet:
1. Dashboard writes to global task board until schema unification is complete.
2. Cron worker against current pending tasks lacking action contracts.

Classification: **Needs stabilization first**.

## 10. System Unification Analysis

### 10.1 Do all parts operate on a single unified model?

No.

### 10.2 Conflicting schemas (dashboard vs worker vs orchestrator)

1. Dashboard task model (`system/dashboard/server.py:63-73`)
- Keys: `id,title,description,priority,status,notes,created_at,updated_at,completed_at`.
- Status enum: `pending|in_progress|complete`.

2. Worker task model (`config/task_schema.json:7-26`, `workers/task_worker.py:276-365`)
- Keys required: `task_id,title,status,priority,action_type`.
- Optional critical: `action_payload`, `correlation_id`.
- Status enum includes `blocked`.

3. Live task data (`~/.claude/tasks.json` sample)
- Uses `task_id`; mostly missing `action_type` and no `id`.

4. Orchestrator run state model (`run_state.json`, `controller.py:105-127`)
- Separate state contract not linked to task board schema.

How they break each other:
- Dashboard drops worker fields when saving.
- Dashboard ID model cannot reliably target worker-native tasks.
- Worker cannot execute dashboard-created tasks without action payload.
- Worker blocked status cannot be represented by dashboard model.

### 10.3 Specific integration breakpoints

1. Where dashboard corrupts/overrides state
- `system/dashboard/server.py:88` writes model dump subset.

2. Where worker ignores dashboard-created data
- Worker expects `action_type/action_payload`; dashboard UI never sets these.

3. Where orchestrator bypasses task system
- Orchestrator runs directly from CLI with plan/goal (`run_cli.py`), independent of task board.

4. Where skills are not actually used in execution
- Deployed runner does not load SKILL.md into execute prompt.

### 10.4 Unified system vs disconnected systems

Current behavior is **disconnected systems sharing files**:
- Dashboard: UI CRUD over tasks file with non-executable schema.
- Worker: action dispatcher requiring executable schema.
- Orchestrator: DAG engine mostly independent of task lifecycle.

### 10.5 Required unified model

1. One task schema
- Canonical ID: `task_id` (string stable key).
- Required execution fields: `action_type`, `action_payload`.
- Lifecycle fields: `status` including `blocked`, timestamps, `attempts`, `last_error`, `correlation_id`.

2. One execution path
- Dashboard creates/edits only canonical task objects.
- Worker claims tasks and executes.
- `run_plan` action bridges task system to orchestrator.
- Orchestrator outputs and emits follow-up tasks through same schema.

3. One source of truth
- Single authoritative `tasks.json` (or DB) with strict schema validation on all writers.

### 10.6 Role boundaries that SHOULD be enforced

1. Dashboard: control plane, not free-form data editor
- Should create/update only validated task contract.
- Should never drop unknown fields.

2. Task system: execution contract
- Owns task identity, status transitions, retry metadata, idempotency.

3. Orchestrator: execution engine
- Consumes `run_plan` tasks and writes run artifacts.
- Emits new tasks through task contract adapter.

## 11. Target Architecture

### 11.1 Unified flow

`user → dashboard → tasks → worker → orchestrator → agents → results → tasks/logs`

Data flow and ownership:
1. User action enters via dashboard API.
2. Dashboard validates against canonical task schema and writes atomic update.
3. Worker polls task board, claims task with optimistic lock/version.
4. If `action_type=run_plan`, worker invokes orchestrator.
5. Orchestrator writes run artifacts and emits follow-up tasks via canonical schema.
6. Worker updates task status and error/metrics fields.
7. Dashboard renders statuses/log links from same source.

Validation points:
- Dashboard write path.
- Worker pre-dispatch parse.
- Orchestrator agent-output validation.
- Merge emitted-task validation.

Execution points:
- Worker dispatcher.
- Orchestrator controller.

### 11.2 One task schema used everywhere

Required canonical fields:
- `task_id` (stable string)
- `title`
- `description`
- `priority` (int 1..5)
- `status` (`pending|in_progress|blocked|complete`)
- `action_type` (`log_only|run_script|generate_file|claude_execute|run_plan`)
- `action_payload` (object)
- `correlation_id` (optional string)
- `created_at`, `updated_at`, `completed_at` (timestamps)
- `attempts`, `last_error` (operational)

### 11.3 File-level keep/refactor/rewrite/delete

Refactor:
1. `system/dashboard/server.py`
- Reason: make schema-preserving I/O with `task_id` primary key, support `blocked`, retain action fields.

2. `system/dashboard/index.html`
- Reason: expose execution fields safely (at minimum action type templates), or prevent non-executable task creation.

3. `workers/task_worker.py`
- Reason: add schema validation, retries/backoff, lock/claim semantics, and consistent correlation propagation.

Rewrite:
1. Deployment sync strategy (`init.sh` + runtime sync checks)
- Reason: current copy model produces drift and partial feature rollout.

2. Contract tests across dashboard/worker/orchestrator
- Reason: no enforcement currently.

Delete (or archive as deprecated once replacements exist):
1. `system/scripts/check_decisions.py` duplicate path if `workers/decision_reviewer.py` remains canonical.
- Reason: overlapping function with no current execution path.

2. Unused/contradictory runtime copies in `~/.claude/system` once canonical runtime location chosen.
- Reason: competing task storage targets.

Keep:
1. `orchestrator/models.py`
- Reason: strongest validation implementation in system.

2. `orchestrator/controller.py` core state tracking
- Reason: useful run-state model.

3. `orchestrator/merge.py` conflict heuristics
- Reason: already useful; just unify deployment and task emission behavior.

4. Dashboard itself
- Reason: required control layer, but must become contract-safe.

### 11.4 Current vs intended divergence

Current:
- File sharing without shared contract.
- Drifted deployments and optional automation.
- Docs overstate execution integration.

Intended:
- Dashboard as reliable control plane.
- Worker as single dispatcher.
- Orchestrator as plan execution backend connected by `run_plan` tasks.

## 12. Prioritized Remediation Plan

### Do now

1. Unify task contract and stop lossy writes
- Problem: dashboard corrupts worker contract.
- Root cause: incompatible Task model and serializer.
- Files: `system/dashboard/server.py`, `system/dashboard/index.html`, `config/task_schema.json`.
- Level: L3/L4.
- Effect: restores control-plane integrity.
- Risk: Medium.
- Verification: round-trip test preserving all fields; dashboard CRUD on existing worker-native tasks.
- Done criteria: no field loss; stable updates by `task_id`.

2. Align deployed runtime with blueprint (single sync cut)
- Problem: runtime drift in worker/orchestrator/skills/plans.
- Root cause: partial/unsupervised sync process.
- Files: `init.sh`, deployed `~/agent-services/*`, `~/.claude/orchestrator/*`, `~/.claude/agents/*`, `~/.claude/skills/*`.
- Level: L2-L4.
- Effect: makes behavior match audited source.
- Risk: High (runtime behavior changes).
- Verification: post-sync `diff -rq` critical directories clean (ignoring caches).
- Done criteria: no critical diffs in executable files.

3. Migrate existing tasks to canonical executable schema
- Problem: pending tasks are non-executable.
- Root cause: legacy/manual task entries without action contract.
- Files: `~/.claude/tasks.json`, project `tasks.json`.
- Level: L4.
- Effect: worker can execute pending queue.
- Risk: High (data migration).
- Verification: 0 pending tasks missing `action_type` and valid payload for non-log tasks.
- Done criteria: schema validator passes 100% of task records.

4. Re-enable worker-orchestrator bridge in deployed worker
- Problem: no `run_plan` action in deployed worker.
- Root cause: stale deployed worker.
- Files: deployed `~/agent-services/workers/task_worker.py`, deployed `config/task_schema.json`.
- Level: L3/L4.
- Effect: tasks can invoke orchestrator.
- Risk: Medium.
- Verification: enqueue `run_plan` task and observe run directory output.
- Done criteria: successful run status and run artifacts generated.

### Do next

1. Add locking/versioning for task board writes
- Problem: race conditions between dashboard and worker writes.
- Root cause: blind file overwrite.
- Files: dashboard + worker task I/O layer.
- Level: L5.
- Effect: prevents state clobbering.
- Risk: Medium.
- Verification: concurrent update test.
- Done criteria: no lost update under concurrent writes.

2. Add end-to-end trace fields
- Problem: weak observability across layers.
- Root cause: no common correlation model.
- Files: dashboard API, worker logs/state, orchestrator run_state.
- Level: L5.
- Effect: auditable execution lineage.
- Risk: Low/Medium.
- Verification: single task traced across all logs.
- Done criteria: one correlation ID present in dashboard task, worker log, run_state, outputs.

3. Make automation activation explicit and verifiable
- Problem: automation assumed but inactive.
- Root cause: no health gating for cron/service status.
- Files: installer scripts + health-check command.
- Level: L5.
- Effect: operational clarity.
- Risk: Low.
- Verification: health command reports cron + process state.
- Done criteria: green health check or explicit inactive state.

### Do later

1. True parallel execution for orchestrator waves
- Problem: declared parallelism is sequential.
- Root cause: no concurrent executor.
- Files: `orchestrator/controller.py`.
- Level: L4.
- Effect: scalability and performance.
- Risk: High (concurrency complexity).
- Verification: deterministic parallel run tests.
- Done criteria: parallel groups execute concurrently with deterministic merge behavior.

2. Consolidate duplicate decision-check scripts
- Problem: duplicated functionality and ambiguous ownership.
- Files: `workers/decision_reviewer.py`, `system/scripts/check_decisions.py`.
- Level: L1/L3.
- Effect: reduce ambiguity.
- Risk: Low.
- Verification: single documented/used checker.
- Done criteria: one canonical script and call path.

### Do not do yet

1. Do not add new agents/plans/features before schema unification
- Why: expands blast radius of broken contract.

2. Do not enable broad autonomous cron execution before migration + locking
- Why: will mass-block or corrupt tasks.

3. Do not remove dashboard
- Why: required control layer; must be fixed, not removed.

## 13. Critical Unknowns That Still Need Proof

1. Whether existing operators rely on `~/.claude/system/dashboard/server.py` (project-root task model) vs `~/agent-services/system/dashboard/server.py` (global task model).
- Needs proof: startup command history or active usage convention.

2. Whether any external automation currently writes tasks with full action contract.
- Needs proof: provenance of recent task entries in `~/.claude/tasks.json`.

3. Whether planned production path intends file-based task store long-term vs migrating to DB-backed queue.
- Needs proof: architecture decision record.

4. Whether worker state dedupe behavior (`processed_tasks`) has caused missed reruns historically.
- Needs proof: historical logs/state snapshots (not present currently).

5. Whether deployed `~/.claude/orchestrator` drift is intentional hotfixing vs unsynced stale copy.
- Needs proof: change process ownership.

## 14. Final Verdict

The system is **not unified**. It is a set of partially connected components with contract drift at the exact seams that matter: dashboard↔tasks↔worker and worker↔orchestrator. There is strong implementation value in parts (notably orchestrator validation), but current operational behavior is dominated by schema mismatch, deployment drift, and inactive automation. The required next move is **stabilization and unification**, not feature expansion: enforce one task contract, align deployed runtime with blueprint, migrate current tasks, and restore a single execution path where dashboard controls, worker executes, orchestrator plans, and all layers share one source of truth.
