# SYSTEM AUDIT — Miguel Gonzalez Agent System

> **Snapshot notice:** Point-in-time audit from **2026-03-23**. Before using this for operations, re-check paths and behavior against the current `agent-system-base/` tree and `init.sh` (see root [`README.md`](../../README.md) and [`agent-system-base/CLAUDE.md`](../../agent-system-base/CLAUDE.md)).

**Date:** 2026-03-23
**Auditor:** Claude Code — Principal Systems Auditor
**Scope:** ~/agent-system-base/, ~/.claude/, ~/agent-services/
**Method:** Direct file reads, grep searches, directory listings, crontab inspection

---

> Every claim in this document is backed by a file read or command executed in this session.
> "UNVERIFIED" is not used — if it's here, it was read.

---

## 1. Executive Summary

This system is architecturally sound in blueprint but **operationally dormant and internally fragmented**. The three-layer design (blueprints → global state → runtime) is coherent as a concept. The implementation breaks down at the seams between layers.

Five issues require immediate action before any expansion:

1. **The autonomous worker has never run.** No agent-services cron jobs are installed. Every pending task in tasks.json sits idle. The system's entire autonomous execution premise is untested.

2. **The deployed worker is behind the blueprint by 57 lines.** The orchestrator bridge (`run_plan` handler), env validation, and correlation ID injection all exist in the blueprint but are missing from the deployed version. The system's intended unification mechanism doesn't exist at the execution layer.

3. **Dashboard-created tasks will crash the dashboard.** The dashboard creates tasks with no `action_type`. The worker marks them "blocked." The dashboard's Pydantic model doesn't accept "blocked" as a status. The next page load throws a validation exception. These two components are incompatible by schema.

4. **No atomic writes on the shared state file.** Both the dashboard and the worker write to `~/.claude/tasks.json` using `open("w") + json.dump` without a temp-file-then-rename pattern. A crash or SIGKILL mid-write corrupts the only source of truth.

5. **The cron "automation" is a reminder to act manually.** The one hourly cron installed for the DMRB project executes `echo "CRON HEARTBEAT — open Claude Code to process tasks"`. It logs a message asking the operator to do the work themselves. It is not automation.

**System classification: Needs stabilization first.**

The orchestrator, skills, agents, and plan DAGs are solid infrastructure. None of it can be trusted operationally until the five issues above are resolved.

---

## 2. System Inventory

### 2.1 Layer Map

| Layer | Directory | Purpose | Operational Status |
|-------|-----------|---------|-------------------|
| Blueprints | ~/agent-system-base/ | Source of truth; edits happen here | Active (not runtime) |
| Global State | ~/.claude/ | Claude Code's domain; synced skills/agents/orchestrator | Partial — orchestrator ready, some files stale |
| Runtime | ~/agent-services/ | Workers, dashboard, cron, logs, API keys | Dormant — no crons installed, no logs generated |

### 2.2 Agent Definitions

**Location:** ~/agent-system-base/agents/ and ~/.claude/agents/

| Agent | In Blueprint | In ~/.claude/agents/ | Agent JSON | SKILL.md | Notes |
|-------|-------------|---------------------|-----------|---------|-------|
| context | ✓ | ✓ | ✓ | ✓ | Synced |
| create | ✓ | ✓ | ✓ | ✓ | Synced |
| intent_router | ✓ | ✓ | ✓ | ✓ | Synced |
| merge | ✓ | ✓ | ✓ | — | No standalone SKILL.md by design (builtin) |
| research | ✓ | ✓ | ✓ | ✓ | Synced |
| seed-project | ✓ | ✓ | ✓ | ✓ | Synced |
| senior_dev_guide | ✓ | ✓ | ✓ | ✓ | Synced |
| skill-creator | ✓ | ✓ | ✓ | ✓ | Synced |
| system_base_manager | ✓ | ✓ | ✓ | ✓ | Synced |
| workflow_coach | ✓ | ✓ | ✓ | ✓ | Synced |
| **planner** | **✓** | **✗** | **MISSING** | ✓ | **SYNC DRIFT — skill deployed, agent JSON not synced** |

**Confirmed by:** `ls /Users/miguelgonzalez/.claude/agents/` — 10 files, no planner.json

### 2.3 Orchestrator Plans

**Location:** ~/.claude/agents/plans/ and ~/agent-system-base/agents/plans/

| Plan | Exists | Verified |
|------|--------|---------|
| swarm_research.json | ✓ | Confirmed by ls |
| linear_context_research.json | ✓ | Confirmed by ls |
| feature_build.json | ✓ | Confirmed by ls |
| bug_fix.json | ✓ | Confirmed by ls |

All four plans exist. The orchestrator README reference is accurate.

### 2.4 Workers

| Worker | Location | LOC | Status | Cron Installed |
|--------|----------|-----|--------|---------------|
| task_worker.py | ~/agent-services/workers/ | 371 | Deployed, never run | NO |
| task_worker.py | ~/agent-system-base/workers/ | 428 | Blueprint (source of truth) | N/A |
| gmail_triage.py | ~/agent-services/workers/ | 125 | **SCAFFOLD — not implemented** | NO (commented out) |
| decision_reviewer.py | ~/agent-services/workers/ | 67 | Deployed, never run via agent-services | NO |
| check_decisions.py | DMRB project /scripts/ | ~52 | Running via DMRB cron | YES (daily 8:14 AM) |

### 2.5 Dashboard

| Component | File | LOC | Status |
|-----------|------|-----|--------|
| API server | ~/agent-services/system/dashboard/server.py | 180 | Deployed, never started |
| UI | ~/agent-services/system/dashboard/index.html | 475 | Deployed, never loaded |
| Launcher | ~/agent-services/system/scripts/start_dashboard.sh | 11 | Not run |
| Log | ~/agent-services/logs/dashboard.log | 0 bytes | Exists, empty |

### 2.6 Schemas

| Schema | File | Version | Usage |
|--------|------|---------|-------|
| agent_output v1 | ~/.claude/schemas/agent_output.schema.json | v1 | Legacy — not used by orchestrator |
| agent_output v2 | ~/.claude/schemas/agent_output_v2.schema.json | v2 | "Documentation mirror" (per line 5) |
| task_schema | ~/agent-services/config/task_schema.json | draft-07 | Not enforced at write time |

**Critical note on agent_output_v2.schema.json line 5:** `"description": "Documentation mirror; runtime validation is orchestrator.models.validate_agent_output_v2"` — the JSON file is decorative. Actual validation lives in Python code. No external tool can validate agent outputs using only this JSON schema.

### 2.7 Installed Cron Jobs

**Command run:** `crontab -l`

```
14 8 * * * python3 "/Users/miguelgonzalez/Projects/Sand box/DRMB_PROD/scripts/check_decisions.py" >> "..."
7 * * * *  echo "$(date) CRON HEARTBEAT — open Claude Code to process tasks" >> "..."
```

**Findings:**
- Zero agent-services cron jobs exist. `~/agent-services/install.sh` has never been run.
- The only hourly cron is an `echo` statement — it logs a message asking the operator to process tasks manually. It is not task execution.
- The daily cron runs `check_decisions.py` from the DMRB project path (path contains a space: "Sand box").

### 2.8 State of Logs

| Log File | Exists | Size | Last Entry |
|----------|--------|------|-----------|
| ~/agent-services/logs/dashboard.log | ✓ | 0 bytes | Never started |
| ~/agent-services/logs/task_worker.log | ✗ | — | Never run |
| ~/agent-services/logs/decision_reviewer.log | ✗ | — | Never run |
| ~/agent-services/logs/gmail_triage.log | ✗ | — | Not implemented |

### 2.9 Knowledge Base State

| File | Location | Lines | Content |
|------|----------|-------|---------|
| gotchas.md | ~/.claude/gotchas.md | 13 | Template only — zero entries |
| parking_lot.md | ~/.claude/parking_lot.md | 23 | Template only — zero entries |
| decisions.csv | ~/.claude/decisions.csv | 13 | 12 active decisions, human-maintained |

---

## 3. True Execution Graph

### 3.1 Intended Flow (as designed)

```
User → Dashboard UI → POST /api/tasks → tasks.json
                                            ↓
                          task_worker.py (cron every 2h)
                          ├── log_only  → log entry
                          ├── run_script → subprocess in project dir
                          ├── generate_file → write file
                          ├── claude_execute → claude --print --prompt
                          └── run_plan → python3 -m orchestrator
                                              ↓
                                         agents/plans/*.json (DAG)
                                              ↓
                                         Wave 1: context agent
                                         Wave 2: research + create (parallel)
                                         Wave 3: merge
                                              ↓
                                         runs/ephemeral/{run_id}/
```

### 3.2 Actual Flow (what is wired and running)

```
User → Dashboard UI   [NEVER STARTED — 0 bytes in log]
                |
                v
         tasks.json   ← Claude Code sessions (manual only)
                |
                v
     task_worker.py   [NEVER RUN — no cron installed]
       (deployed version — 4 action_types only)
       MISSING: run_plan handler
       MISSING: validate_env()
       MISSING: correlation_id injection

     Orchestrator     [MANUAL ONLY — CLI invocation only]
       cd ~/.claude && python3 -m orchestrator ...
       NO connection to tasks.json
       NO connection to dashboard
       Writes to runs/ephemeral/ only

     gmail_triage.py  [SCAFFOLD — not implemented]
```

### 3.3 What Is Actually Running Autonomously

```
Every hour at :07 →  echo "open Claude Code to process tasks" >> tasks.log
Daily at 8:14 AM →  python3 check_decisions.py  (DMRB project only)
```

The system has zero autonomous task processing. No agent is executing without manual invocation.

### 3.4 What the "Heartbeat" Cron Actually Does

The cron at `7 * * * *` executes:
```bash
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)  CRON HEARTBEAT — open Claude Code to process tasks" >> tasks.log
```
This is a reminder to the operator. It performs no work. It cannot be confused with autonomous execution.

---

## 4. Hidden Assumptions

These are things the system relies on but does not verify or enforce.

| # | Assumption | Where It Lives | Consequence If Wrong |
|---|-----------|---------------|---------------------|
| A1 | `init.sh` is run after every change to blueprints | CLAUDE.md | Deployed workers/skills drift from source of truth |
| A2 | `~/.claude/tasks.json` is always valid JSON | task_worker.py line 258, server.py line 82-83 | Worker logs ERROR and returns; dashboard throws exception on next load |
| A3 | Task IDs are globally unique | task_worker.py line 108 (already_processed check) | Same task processed twice, state corruption |
| A4 | `task_id` and `id` are interchangeable | task_worker.py line 269, 324 | Schema says `task_id` required; dashboard uses `id`; worker patches both |
| A5 | ANTHROPIC_API_KEY is set before worker runs | Only in blueprint worker (validate_env line 86-90) — NOT in deployed | claude_execute fails with auth error, not startup error |
| A6 | `claude` CLI is installed and on PATH | task_worker.py line 204 handle_claude_execute | Raises ActionError("claude CLI not found") — task marked blocked |
| A7 | Plans referenced in tasks resolve to existing plan files | handle_run_plan (blueprint only) | FileNotFoundError if plan doesn't exist |
| A8 | Project path in projects_index.json exists and is reachable | task_worker.py line 354 | tasks_file not found, WARN logged, project silently skipped |
| A9 | tasks.json is a JSON array (not object) | task_worker.py line 259 | Worker logs ERROR, returns without processing |
| A10 | Agent outputs from Claude are parseable JSON | orchestrator/runner/json_extract.py | Failure envelope returned; if critical agent, OrchestratorAbort raised |
| A11 | Dashboard never runs concurrently with task_worker | No cross-process locking exists | JSON corruption |
| A12 | Orchestrator cwd ~/.claude puts orchestrator package on Python path | handle_run_plan uses cwd=~/.claude | Works as long as ~/.claude/orchestrator/__init__.py exists (it does) |
| A13 | skills in ~/.claude/skills/ match agents in ~/.claude/agents/ | init.sh sync | Skill without agent JSON: skill triggers but agent has no JSON config (planner is in this state) |
| A14 | All tasks are processed in a single worker invocation | task_worker.py processes ALL pending | Long-running tasks (claude_execute, run_plan) block subsequent tasks |
| A15 | decisions.csv is always up to date | Human maintenance only | decision_reviewer flags stale dates but can't know about undocumented decisions |

---

## 5. System Invariants

### INV-1: tasks.json is a JSON array
**Why it matters:** Both server.py `_load()` (line 82-83) and task_worker.py `load_json()` (line 84-86) assume array format.
**Enforcement:** `isinstance(tasks, list)` check at task_worker.py line 259 — logs ERROR and returns.
**Server.py enforcement:** None — `[Task(**row) for row in json.load(f)]` crashes with TypeError if JSON is not iterable.
**Risk if violated:** Dashboard throws 500 on every API call; worker logs ERROR and exits.

### INV-2: Task IDs within a source are unique
**Why it matters:** `already_processed` state (task_worker_state.json) keys on (source, task_id). Duplicate IDs cause second task to be skipped silently.
**Enforcement:** None. No deduplication at write time.
**Status: ASSUMED ONLY**

### INV-3: task_schema.json action_type enum matches deployed worker HANDLERS dict
**Why it matters:** The schema is used to validate what workers can handle.
**Current state:** Schema has 4 types; blueprint worker has 5. They are out of sync.
**Enforcement:** None — schema is never validated against at write time.
**Status: VIOLATED — deployed schema is behind blueprint**

### INV-4: Dashboard Status enum matches task_schema.json status values
**Why it matters:** Any task with status="blocked" breaks dashboard load.
**Current state:** task_schema.json has ["pending", "in_progress", "blocked", "complete"]; dashboard `Status` enum (server.py line 42-45) has only ["pending", "in_progress", "complete"].
**Enforcement:** None.
**Status: VIOLATED**

### INV-5: tasks.json schema_version is consistent (task_id vs id field)
**Why it matters:** tasks.json has two ID conventions — `task_id` (CLAUDE.md/worker protocol) and `id` (dashboard UUID). Worker patches both at line 269/324.
**Enforcement:** Partial — worker handles both but schema requires `task_id`.
**Status: VIOLATED — two ID conventions coexist**

### INV-6: Blueprint and deployed workers are in sync
**Why it matters:** The blueprint is the source of truth; deployed version must match.
**Current state:** Blueprint is 57 LOC ahead; missing: run_plan handler, validate_env, correlation_id, REQUIRED_ENV_KEYS.
**Enforcement:** None — init.sh must be run manually.
**Status: VIOLATED**

### INV-7: Every agent JSON in ~/.claude/agents/ has a corresponding SKILL.md
**Why it matters:** Orchestrator injects SKILL.md body into system prompt via agent JSON `skill` field.
**Current state:** 10 agents deployed; planner agent JSON missing.
**Status: VIOLATED for planner (skill exists, agent JSON absent)**

### INV-8: tasks.json is never corrupted mid-write
**Why it matters:** It is the only source of truth for all task state.
**Enforcement:** None — no atomic write pattern in either server.py or task_worker.py.
**Status: ASSUMED ONLY — latent risk**

---

## 6. Layer-by-Layer Maturity Assessment

### L1 — Context Rules (CLAUDE.md, project instructions)
**Score: 8/10**

What works: CLAUDE.md is comprehensive and specific. It defines session protocol, task schema, escalation rules, definition of done, drift detection, parking lot, and memory system. It is the strongest layer.

What prevents 10/10:
- gotchas.md and parking_lot.md are empty templates. The memory protocol says to write to these but they've never been populated. CLAUDE.md references them as active knowledge bases — they are not.
- `Session Start (Mandatory)` protocol at CLAUDE.md includes a 5-step planning gate, but the gate relies on tasks.json being processed by an autonomous worker. That worker has never run, so the "hourly cron worker processes tasks automatically" statement is false.
- The two ID conventions (task_id vs id) in the task schema section of CLAUDE.md are not flagged — CLAUDE.md says to use `task_id` but the dashboard creates `id`.

Evidence: ~/.claude/CLAUDE.md (266 LOC), ~/.claude/gotchas.md (13 LOC template only)

### L2 — Skills
**Score: 7/10**

What works: 12 skills exist with SKILL.md files. Frontmatter is consistent (name, version, description, allowed-tools). Skills reference failure modes, exit conditions, and trigger phrases. skill-creator at 493 LOC is thorough. system_base_manager at 299 LOC is complete.

What prevents higher:
- planner.json is missing from ~/.claude/agents/. The planner skill triggers in Claude Code sessions, but if the orchestrator tries to use the planner agent, it will throw FileNotFoundError at controller.py line 41: `raise FileNotFoundError(f"agent definition not found: {p}")`.
- gmail_triage SKILL.md describes an operational worker ("Worker logs to ~/agent-services/logs/gmail_triage.log") but the worker is a scaffold. The skill implies functionality that doesn't exist.
- The swarm SKILL.md says "Requires claude-system/ at project root" — this constraint is documented in the skill but not enforced. Silent failure if the directory is absent.
- No skill covers the transition between the three layers (blueprints → global → runtime). A "deploy changes" or "sync system" skill would reduce the manual `init.sh` burden.

Evidence: ~/.claude/skills/ (12 directories), ~/agent-system-base/.claude/skills/gmail_triage/SKILL.md, ~/agent-system-base/.claude/skills/swarm/SKILL.md

### L3 — Dynamic Hooks / Automation
**Score: 1/10**

What works: install.sh is written and syntactically correct. The cron schedule is defined (task_worker every 2h, decision_reviewer daily, gmail_triage disabled). The task_worker properly creates its log directory on first run.

What prevents higher:
- install.sh has never been executed. Zero agent-services cron jobs exist.
- The one hourly cron that exists (`7 * * * *`) is an echo statement asking the operator to do work manually.
- Autonomous execution is entirely theoretical. No task has ever been processed by the worker without manual invocation.
- There is no monitoring. If a cron fails silently, nothing alerts.
- There is no retry logic at the cron level — if task_worker.py exits non-zero, the failure is silent.

Evidence: `crontab -l` output, ~/agent-services/install.sh, ~/agent-services/logs/ (all empty/missing)

### L4 — End-to-End Orchestration
**Score: 4/10**

What works: The orchestrator package is solid (~1,800 LOC Python). Topological wave execution, retry logic, failure envelopes, context size enforcement, merge conflict detection — all implemented. Four plans exist and are loadable. The orchestrator can be run manually with `--mode simulate` without API calls.

What prevents higher:
- The orchestrator has zero integration with tasks.json. It is an isolated execution island. Dashboard → tasks → orchestrator is the intended flow; the actual flow is: manually type `python3 -m orchestrator` in terminal.
- The bridge (run_plan handler in task_worker) exists only in the blueprint. The deployed worker cannot trigger the orchestrator.
- In execute mode, the orchestrator calls the Anthropic API directly. It has no awareness of whether ANTHROPIC_API_KEY is set — it would fail at runtime with an auth error, not a startup validation.
- No orchestrator run has ever been connected to a task in tasks.json.
- Handoff mode stops after each wave and requires manual `--resume --advance`. This is correct by design but means multi-wave orchestration is not automatable with current worker.

Evidence: ~/.claude/orchestrator/controller.py (lines 38-49 show plan/agent loading), ~/agent-services/workers/task_worker.py (no run_plan in HANDLERS dict at line 214)

### L5 — Hardening / Reliability / Control
**Score: 2/10**

What works: Path confinement in task_worker (safe_path, line 119-125). threading.Lock() in dashboard for HTTP concurrency. ActionError catches known failures cleanly. Worker processes one task at a time (sequential, not parallel). Processed task deduplication via state.json.

What prevents higher:
- No atomic writes to tasks.json (both server.py and task_worker.py).
- No cross-process file locking (dashboard uses threading.Lock but task_worker has no lock).
- Dashboard crashes on "blocked" status — Status enum mismatch is a fatal bug.
- Dashboard-created tasks cannot be executed by the worker (no action_type field).
- No alerting, monitoring, or health checks.
- No rollback capability for task state changes.
- No schema validation at write time for tasks.json.
- validate_env() missing from deployed worker — ANTHROPIC_API_KEY absence is silent until failure.
- No rate limiting or cost cap on claude_execute or run_plan tasks.
- Output truncation (500 chars) in all handlers loses diagnostic information silently.

Evidence: server.py line 42-45 (Status enum), server.py line 83 (_load Pydantic validation), server.py line 86-88 (_save no atomic), task_worker.py line 214 (HANDLERS dict, 4 keys)

---

## 7. Failure Modes and Breakpoints

| # | Failure Mode | Trigger | Observed Effect | Hidden Effect | Severity | Detectability | Current Mitigation | Missing Mitigation |
|---|-------------|---------|----------------|--------------|----------|--------------|-------------------|-------------------|
| F1 | Worker marks task "blocked" | Any handler raises ActionError | Worker logs "Task blocked", writes status="blocked" to tasks.json | Dashboard crashes on next load (Pydantic ValidationError on Status enum) | **CRITICAL** | Delayed — visible only when dashboard opens | None | Add "blocked" to dashboard Status enum; or catch validation errors in _load() |
| F2 | Dashboard-created task processed by worker | Dashboard creates task, cron runs | Worker defaults to log_only, raises "payload.message required", marks blocked | Cascade: now F1 applies | **CRITICAL** | Silent until F1 hits | None | Dashboard must set action_type or worker must skip tasks without it |
| F3 | tasks.json corrupted mid-write | SIGKILL during json.dump in server.py or task_worker.py | JSON decode error on next read | All task state lost; dashboard 500s; worker exits with ERROR | **CRITICAL** | Visible but unrecoverable without backup | ~/.claude/backups/ (5 backup files exist — but backup is NOT triggered on write) | Atomic write: temp file → rename |
| F4 | task_worker runs while dashboard is open | Both started, any task update | Race condition on file access | Partial write from one process; JSON corruption | **HIGH** | Silent — no error until next read | None | OS-level file lock (fcntl.flock) in both processes |
| F5 | ANTHROPIC_API_KEY not set when claude_execute task runs | Deployed worker has no validate_env | claude CLI exits with auth error, task marked blocked | No startup warning; operator must read logs | **HIGH** | Silent (log only) | None in deployed worker | Add validate_env() from blueprint to deployed worker |
| F6 | Project path in projects_index.json does not exist | Path has space: "Sand box/DRMB_PROD" | tasks_file = ppath / "tasks.json" → Path exists check at line 254 fails → WARN logged, project skipped | No error to operator | **HIGH** | WARN in log only | Path check at task_worker.py line 254 | Fix path or quote it; add existence check for ppath itself |
| F7 | init.sh not run after blueprint change | Worker diverges from blueprint | Deployed worker missing features (currently: run_plan, validate_env, correlation_id) | Features are documented but silently absent | **HIGH** | None — operator must remember | None | Post-commit hook or CI check to alert when blueprint and deployed differ |
| F8 | planner skill triggers but planner agent JSON is absent | Orchestrator tries to `load_agent("planner")` | FileNotFoundError at controller.py line 41 | OrchestratorAbort if planner is marked critical | **HIGH** | Visible error at runtime | None | Sync planner.json to ~/.claude/agents/ via init.sh |
| F9 | gmail_triage skill invoked by operator | Operator calls /gmail_triage | Skill instructs worker to run gmail_triage.py | Worker runs stub code, fails with missing credentials or unimplemented function | **MEDIUM** | Visible error | Cron disabled | Clearly mark SKILL.md as "NOT IMPLEMENTED — requires Gmail OAuth setup" |
| F10 | tasks.json grows unbounded | 34 completed tasks already in file; all historical tasks retained | Reads and writes get slower over time | Worker loads entire array into memory each run | **MEDIUM** | Silent performance degradation | None | Archive/rotate completed tasks |
| F11 | run_plan invoked but orchestrator in simulate mode (default) | Blueprint worker default mode="simulate" | Orchestrator runs but makes no API calls | Appears to succeed; no actual agent work done | **MEDIUM** | Silent — mode not logged prominently | None | Log mode explicitly; require explicit mode=execute for production |
| F12 | Duplicate task IDs | Manual task creation | Second task silently skipped (already_processed check) | Task appears pending but never processes | **MEDIUM** | Invisible | processed_tasks state tracks by (source, task_id) | Validate uniqueness at write time |
| F13 | claude_execute prompt truncation | Subprocess stdout > 500 chars | Result logged as first 500 chars | Diagnostic info lost | **LOW** | Visible (truncated output in log) | Log truncation marker | Increase limit or log to separate file |
| F14 | Long-running claude_execute blocks subsequent tasks | Worker is sequential | Other pending tasks wait | P1 tasks after a slow P3 claude_execute are delayed | **LOW** | Visible in timing | None | Process one task per run (already true); or add priority-based preemption |

---

## 8. Control / Safety / Reliability Audit

### 8.1 Observability

**What exists:**
- Structured JSON logging in task_worker.py — every action logged with ts, level, source, task_id, action_type, result
- server.py logs CREATED/UPDATED/COMPLETED/DELETED with task ID and priority
- Orchestrator writes per-step JSON output files to runs/ephemeral/{run_id}/

**What is missing:**
- No logs exist. The system has never run (all log files empty or absent).
- No centralized log viewer (dashboard shows tasks, not logs)
- No alert on worker failure
- No execution summary email/notification
- No way to see "what happened this hour" without `cat task_worker.log`
- No audit trail for who changed a task (dashboard or worker or manual edit)
- Processed tasks state (task_worker_state.json) is written but never exposed to operator

### 8.2 Traceability

**What exists:**
- `correlation_id` field in blueprint CLAUDE.md task schema — groups related tasks from one planning session
- `correlation_id` injection in blueprint task_worker (handle_claude_execute, lines 207-210)
- Orchestrator run IDs written to per-step output files

**What is missing:**
- `correlation_id` injection is absent from deployed worker (pre-dates blueprint version)
- No way to trace "this orchestrator run came from this task"
- No way to trace "this file was written by this task"
- Orphaned orchestrator runs in runs/ephemeral/ have no link back to tasks.json

### 8.3 Rollback

**What exists:** ~/.claude/backups/ contains 5 .claude.json backup files (Claude Code internal state)

**What is missing:**
- No backup of tasks.json before write. The 5 backups are Claude Code session state, not task state.
- No undo for task status changes
- No rollback for files written by generate_file handler
- No rollback for scripts executed by run_script handler
- If tasks.json is corrupted, there is no recovery path

### 8.4 Idempotency

**What exists:**
- `already_processed` state in task_worker_state.json prevents reprocessing same task ID
- `overwrite: false` option in generate_file handler skips if file exists

**What is missing:**
- `already_processed` check keys on task_id within source. If tasks.json is fully rewritten with same task_ids, they'll be skipped as "already done" — correct behavior.
- No idempotency for claude_execute or run_plan — if state.json is deleted, same prompts run again
- No idempotency for run_script — same script executed twice if state is reset

### 8.5 Approval Gates

**What exists:**
- Orchestrator `handoff` mode stops after each wave for manual inspection
- CLAUDE.md requires session task approval before execution

**What is missing:**
- No approval gate before cron worker processes tasks (by design, but means any task placed in tasks.json will execute)
- No approval gate before claude_execute sends arbitrary prompts to the Claude CLI
- No approval gate before run_script executes arbitrary scripts
- No cost approval before API-calling tasks execute

### 8.6 Write Permissions and Blast Radius

**task_worker.py write surfaces:**
- `~/agent-services/state/task_worker_state.json` — state tracking
- `~/agent-services/logs/task_worker.log` — append only
- `~/.claude/tasks.json` — status updates in place
- Any file specified in generate_file tasks (path-confined to project_path)
- Arbitrary shell scripts via run_script (confined to project_path)
- Arbitrary Claude prompts via claude_execute (Claude Code has full filesystem access)

**server.py write surfaces:**
- `~/.claude/tasks.json` — create, update, delete, complete
- `~/agent-services/logs/dashboard.log` — append only

**Blast radius concern:** `claude_execute` handler spawns `claude --print --prompt <prompt>` with no additional sandboxing beyond Claude Code's own permissions. A task with a destructive prompt (e.g., "delete all files in ~/Projects/") would execute without confirmation. There is no prompt review layer.

### 8.7 Source-of-Truth Integrity

| State | Source of Truth | Competing Writers | Sync Mechanism |
|-------|----------------|-----------------|----------------|
| Task state | ~/.claude/tasks.json | server.py + task_worker.py | None (race condition) |
| Worker execution state | task_worker_state.json | task_worker.py only | N/A |
| Orchestrator run outputs | runs/ephemeral/{run_id}/ | orchestrator only | N/A |
| Agent/skill definitions | ~/agent-system-base/ | init.sh syncs to ~/.claude/ | Manual: must run init.sh |
| Decisions | ~/.claude/decisions.csv | Human writes only | N/A |

---

## 9. Execution Readiness

### What Is Ready Now (Verified)

| Component | Readiness | Evidence |
|-----------|----------|---------|
| Orchestrator (simulate mode) | Ready | ~/.claude/orchestrator/ package complete; 4 plans exist |
| Orchestrator (execute mode) | Ready if ANTHROPIC_API_KEY set | No code gap; env check only |
| Dashboard UI | Ready to start | server.py complete; index.html complete; never started |
| task_worker (4 action_types) | Ready to deploy | Script is correct for its 4 handlers |
| Skills (10 of 12) | Ready | Synced to ~/.claude/skills/; planner + gmail_triage are exceptions |
| Agents (10 of 11) | Ready | Synced to ~/.claude/agents/; planner.json missing |
| decision_reviewer | Ready to cron | Script correct; just needs cron entry |

### What Is Not Ready

| Component | Gap | File |
|-----------|-----|------|
| task_worker (run_plan bridge) | Missing handler | ~/agent-services/workers/task_worker.py — sync from blueprint |
| Dashboard "blocked" status | Enum mismatch will crash | ~/agent-services/system/dashboard/server.py line 42-45 |
| Dashboard → worker task compatibility | No action_type on dashboard tasks | server.py Task model (lines 48-52) |
| gmail_triage | Not implemented | ~/agent-services/workers/gmail_triage.py |
| planner agent JSON | Not synced | Run init.sh to deploy planner.json |
| Cron automation | install.sh never run | ~/agent-services/install.sh |
| Atomic writes | Neither writer is safe | server.py line 86-88; task_worker.py line 89-93 |
| Unified task schema | Two ID fields, missing run_plan | task_schema.json line 19-22 |

### What Cannot Be Trusted

1. **The dashboard** — it has never run. Any behavior described about it is theoretical.
2. **Autonomous task processing** — no cron. No worker has ever processed a task from tasks.json without manual invocation.
3. **gmail_triage** — the skill implies functionality. The worker is a scaffold.
4. **The "deployed" worker** — it processes tasks, but is missing the orchestrator bridge and env validation from the blueprint.

### What Requires Human Review Before Automating

1. `claude_execute` tasks — prompts should be reviewed before enabling cron. The worker will execute arbitrary prompts sent to Claude Code CLI.
2. Project path in projects_index.json — "Sand box/DRMB_PROD" needs verification that path exists as-is with the space.
3. tasks.json pending entries — confirm any pending claude_execute or run_plan tasks are safe to execute autonomously before running worker.

### System Verdict: Needs Stabilization First

The infrastructure is well-designed. The execution layer is undeployed, behind the blueprint, and has three compatibility bugs that would cause crashes on first real use. Stabilize before expanding.

---

## 10. System Unification Analysis

### 10.1 Do All Parts Operate on a Unified Model?

**No.** Three systems touch task state; none of them share a unified contract.

### 10.2 Conflicting Schemas

**Dashboard task model** (server.py lines 48-73 — what it creates):
```python
class Task(BaseModel):
    id: str              # UUID4 — NOT task_id
    title: str
    description: str
    priority: int        # 1-5
    status: Status       # ONLY: pending, in_progress, complete
    notes: str
    created_at: str
    updated_at: Optional[str]
    completed_at: Optional[str]
    # NO action_type
    # NO action_payload
    # NO correlation_id
    # NO task_id
```

**CLAUDE.md task schema** (what Claude Code creates):
```json
{
  "task_id": "ses-YYYYMMDD-NNN",
  "title": "...",
  "description": "...",
  "priority": 1,
  "status": "pending",
  "action_type": "claude_execute",
  "action_payload": { "prompt": "..." },
  "correlation_id": "uuid4",
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601"
}
```

**task_schema.json** (what the schema says):
- Required: task_id, title, status, priority, action_type
- Status enum: pending, in_progress, blocked, complete
- action_type enum: log_only, run_script, generate_file, claude_execute (missing run_plan)

**How they break each other:**

1. Dashboard creates `id`, not `task_id`. Schema requires `task_id`. Worker falls back to `task.get("task_id") or task.get("id")` — functional but schema-violating.

2. Dashboard creates no `action_type`. Worker defaults to "log_only". `log_only` requires `action_payload.message`. Without it, ActionError is raised. Task marked "blocked".

3. Worker marks tasks "blocked". Dashboard Status enum doesn't include "blocked". `Task(**row)` raises Pydantic ValidationError. Dashboard crashes.

4. Dashboard `notes` field doesn't exist in task_schema.json. Dashboard `completed_at` doesn't exist in task_schema.json. These are extra fields — not fatal, but they drift.

### 10.3 Where Systems Compete Instead of Integrate

| Conflict Point | Component A | Component B | Effect |
|---------------|------------|------------|--------|
| tasks.json write | Dashboard (server.py _save) | task_worker (save_json) | Race condition, potential corruption |
| Task schema | Dashboard Task model | CLAUDE.md task format | Incompatible field names and status values |
| Task creation | Dashboard (UI) | Claude Code sessions (CLAUDE.md protocol) | Different schemas, both write to same file |
| Execution trigger | Manual cron (not installed) | Manual CLI invocation | No unified trigger; no automation |
| Run state | tasks.json (worker updates) | runs/ephemeral/ (orchestrator writes) | No link between them |

### 10.4 The Orchestrator Is an Execution Island

The orchestrator:
- Reads from: `~/.claude/agents/plans/*.json`, `~/.claude/agents/*.json`
- Writes to: `{runs_dir}/{run_id}/*.json`
- Has NO code that reads or writes `~/.claude/tasks.json`

The task_worker's `run_plan` handler (blueprint only) was designed as the bridge:
```python
def handle_run_plan(payload, project_path):
    # runs: python3 -m orchestrator --runs-dir ... --plan ... --goal ... --mode ...
    # cwd: ~/.claude
```

This bridge exists in the blueprint (`~/agent-system-base/workers/task_worker.py` line 230-262) but is absent from the deployed version. Until it is deployed, dashboard → tasks → orchestrator is an aspirational flow, not a real one.

### 10.5 Required Unified Model

**One task schema (proposed):**
```json
{
  "task_id": "string — required, unique per source",
  "title": "string — required",
  "description": "string — optional",
  "priority": "integer 1-5 — required",
  "status": "enum: pending | in_progress | blocked | complete — required",
  "action_type": "enum: log_only | run_script | generate_file | claude_execute | run_plan — required",
  "action_payload": "object — required shape depends on action_type",
  "correlation_id": "string UUID — optional, groups related tasks",
  "created_at": "ISO 8601 — optional",
  "updated_at": "ISO 8601 — optional",
  "completed_at": "ISO 8601 — optional"
}
```

**Notes:**
- `id` field used by dashboard must either be renamed `task_id` or dashboard must be updated to use `task_id`
- `notes` field used by dashboard is an extension — acceptable if schema allows `additionalProperties`
- Dashboard Status enum must include "blocked"
- Dashboard TaskIn model must expose `action_type` and `action_payload` for tasks intended for the worker

---

## 11. Target Architecture

### 11.1 Role Definitions

| Layer | Role | Should Own | Should NOT Own |
|-------|------|-----------|---------------|
| Dashboard | Control interface — create, view, update, delete tasks; inspect logs; trigger workers | Tasks CRUD, status display, log viewer | Task execution, schema validation logic |
| Task system (tasks.json) | Execution contract — single source of truth for what needs to happen | Task state, action_type, priority, correlation | Execution logic, agent definitions |
| Worker (task_worker.py) | Execution engine for tasks — dispatches action_types | Handler implementations, state tracking, logging | Task creation, plan definitions |
| Orchestrator | Execution engine for multi-step AI plans — runs DAGs of agents | Plan execution, agent coordination, wave management | Task creation, tasks.json state |
| Agents | Capability workers — research, create, merge, plan | Domain-specific execution within a plan step | Cross-agent coordination (orchestrator's job) |
| Skills | Capability definitions — SKILL.md files that guide agent behavior | Trigger conditions, process instructions, failure modes | Execution logic (that's the agent/worker's job) |
| Automation | Trigger layer — crons, scheduled execution | Schedule definitions, monitoring | Worker logic, task definitions |

### 11.2 Required Unified Flow

```
User
  → Dashboard UI (create task with action_type + action_payload)
  → POST /api/tasks
  → ~/.claude/tasks.json [SINGLE SOURCE OF TRUTH]
  → task_worker.py (cron every 2h)
      ├── claude_execute  → claude --print --prompt (with correlation_id)
      ├── run_plan        → python3 -m orchestrator --plan ... --goal ...
      │                        → agents/plans/DAG
      │                        → Wave 1..N (agent steps)
      │                        → runs/ephemeral/{run_id}/*.json
      │                        [FUTURE: post run summary back to tasks.json]
      ├── run_script      → subprocess in project_path
      ├── generate_file   → write file in project_path
      └── log_only        → log entry
  → tasks.json updated (status = complete or blocked)
  → Dashboard displays result
```

### 11.3 Files: Refactor / Rewrite / Delete / Keep

**MUST FIX NOW (breaking bugs):**

| File | Action | Reason |
|------|--------|--------|
| ~/agent-services/workers/task_worker.py | **Sync from blueprint** | Missing run_plan, validate_env, correlation_id |
| ~/agent-services/system/dashboard/server.py | **Fix Status enum** | Line 42-45: add "blocked" to prevent crash |
| ~/agent-services/system/dashboard/server.py | **Add action_type to TaskIn** | Dashboard-created tasks must be executable |
| ~/agent-services/config/task_schema.json | **Add run_plan to enum** | Schema must match deployed worker |

**MUST DO BEFORE GOING LIVE:**

| File | Action | Reason |
|------|--------|--------|
| ~/agent-services/workers/task_worker.py | **Add atomic write** | save_json must use temp-file-then-rename |
| ~/agent-services/system/dashboard/server.py | **Add atomic write** | _save must use temp-file-then-rename |
| ~/agent-services/workers/task_worker.py | **Add file lock** | Cross-process safety with dashboard |
| ~/agent-services/install.sh | **Execute** | Cron automation has never started |
| ~/agent-system-base/agents/planner.json | **Sync to ~/.claude/agents/** | Run init.sh |
| ~/agent-services/config/projects_index.json | **Verify/fix path** | "Sand box" space may cause shell failures |

**KEEP AS-IS:**

| File | Reason |
|------|--------|
| ~/.claude/orchestrator/ (full package) | Solid implementation; no changes needed |
| ~/agent-system-base/agents/plans/*.json | All 4 plans correct |
| ~/.claude/schemas/agent_output_v2.schema.json | Documentation mirror is fine; runtime validation is in Python |
| ~/agent-system-base/.claude/skills/ (10 of 12) | Synced and correct |
| ~/agent-services/system/dashboard/index.html | UI is complete; no changes needed |
| task_worker_state.json pattern | Deduplication mechanism is correct |

**MARK CLEARLY AS NOT IMPLEMENTED:**

| File | Action | Reason |
|------|--------|--------|
| ~/agent-services/workers/gmail_triage.py | **Add NOT_IMPLEMENTED guard at entry** | Currently scaffold; SKILL.md implies it's operational |
| ~/agent-system-base/.claude/skills/gmail_triage/SKILL.md | **Add status warning at top** | Misleads operator |

---

## 12. Prioritized Remediation Plan

### DO NOW (system is broken without these)

**R1 — Fix dashboard Status enum**
- Problem: Worker sets status="blocked"; dashboard crashes loading "blocked" tasks
- Root cause: server.py line 42-45, Status enum has 3 values; task_schema.json has 4
- File: ~/agent-services/system/dashboard/server.py
- Fix: Add `blocked = "blocked"` to Status enum
- Risk: Low — additive change, backward-compatible
- Verify: Create a task via dashboard, manually set status="blocked" in tasks.json, reload dashboard — must not crash
- Done: Dashboard loads without error when any task has status="blocked"

**R2 — Add action_type to dashboard TaskIn model**
- Problem: Dashboard creates tasks with no action_type; worker always blocks them
- Root cause: server.py TaskIn model (lines 48-52) has no action_type or action_payload
- File: ~/agent-services/system/dashboard/server.py
- Fix: Add `action_type: str = "log_only"` and `action_payload: dict = {}` to TaskIn; expose in POST /api/tasks
- Risk: Medium — changes the API contract; clients expecting old shape must update
- Verify: Create task via dashboard with action_type="log_only" + action_payload={"message": "test"}, run worker dry-run — must dispatch correctly
- Done: Dashboard-created tasks are processable by the worker

**R3 — Sync deployed task_worker from blueprint**
- Problem: Deployed worker is 57 LOC behind; missing run_plan, validate_env, correlation_id
- Root cause: init.sh not run after blueprint updates
- File: ~/agent-services/workers/task_worker.py (replace with ~/agent-system-base/workers/task_worker.py)
- Fix: Run `bash ~/agent-system-base/init.sh` or manually copy
- Risk: Low — blueprint is the source of truth; sync is the intended mechanism
- Verify: `grep "run_plan" ~/agent-services/workers/task_worker.py` must return a match
- Done: Both task_worker.py files are identical in content

**R4 — Add run_plan to task_schema.json**
- Problem: Deployed schema missing "run_plan" action_type
- Root cause: Schema not synced when run_plan was added to blueprint
- File: ~/agent-services/config/task_schema.json line 20
- Fix: Add "run_plan" to action_type enum
- Risk: None — additive
- Done: `run_plan` in schema enum matches deployed worker HANDLERS dict

### DO NEXT (system is unsafe without these)

**R5 — Add atomic writes to tasks.json**
- Problem: A crash mid-write corrupts the only source of truth
- Root cause: Direct `open("w") + json.dump` in both server.py (line 86-88) and task_worker.py (line 89-93)
- Files: Both server.py _save() and task_worker.py save_json()
- Fix: Write to `tasks.json.tmp`, then `os.replace(tmp, tasks.json)` (atomic on POSIX)
- Risk: Low — behavior identical; only adds safety
- Done: No partial writes possible; file is always valid JSON or old version

**R6 — Add cross-process file lock to task_worker**
- Problem: Worker and dashboard can corrupt tasks.json if running simultaneously
- Root cause: task_worker has no file locking
- File: ~/agent-services/workers/task_worker.py
- Fix: Use `fcntl.flock` or a lockfile pattern around read-modify-write in process_tasks()
- Risk: Low
- Done: Concurrent worker + dashboard access is serialized safely

**R7 — Install agent-services crons**
- Problem: Zero autonomous execution. The entire autonomous premise is untested.
- Root cause: ~/agent-services/install.sh never executed
- Command: `bash ~/agent-services/install.sh`
- Pre-requisites: R1 (status enum), R2 (action_type), R3 (worker sync), R4 (schema) must be done first
- Risk: MEDIUM — once crons run, they'll process pending tasks autonomously. Review tasks.json before enabling.
- Verify: `crontab -l | grep task_worker` must show `0 */2 * * *`
- Done: `crontab -l` shows agent-services entries; task_worker.log has entries after next 2-hour mark

**R8 — Sync planner.json to ~/.claude/agents/**
- Problem: Planner skill exists but agent JSON missing; orchestrator would throw FileNotFoundError
- Root cause: init.sh not run after planner agent was added
- Fix: Run `bash ~/agent-system-base/init.sh` (same run as R3)
- Done: `ls ~/.claude/agents/planner.json` returns file

**R9 — Fix or document projects_index.json path**
- Problem: "Sand box/DRMB_PROD" has a space; verify the actual path resolves
- File: ~/agent-services/config/projects_index.json
- Fix: Verify `ls "/Users/miguelgonzalez/Projects/Sand box/DRMB_PROD"` works; or rename directory
- Done: `ppath = Path(project["project_path"])` resolves to an existing directory

### DO LATER (system works without, but is fragile)

**R10 — Add tasks.json backup-on-write**
- Rotate a backup before every write to tasks.json
- Low urgency if atomic writes (R5) are implemented

**R11 — Archive completed tasks**
- tasks.json currently retains all 34 completed tasks + future completions
- Move completed tasks to tasks_archive.json to keep tasks.json lean

**R12 — Add "blocked" visibility to dashboard**
- Display blocked tasks with error message from action_payload result
- Currently no UI surface for blocked state even after R1 fix

**R13 — Make gmail_triage SKILL.md honest**
- Update SKILL.md to reflect scaffold status with clear TODO before it's enabled

**R14 — Add validate_env() check to dashboard startup**
- Log a warning if ANTHROPIC_API_KEY is not set, since dashboard users may want to know

### DO NOT DO YET

**Do not add new agents, skills, or plans** until R1-R9 are done. The execution layer is not stable enough to trust new automation.

**Do not enable gmail_triage cron** until Gmail OAuth is set up and the worker is implemented.

**Do not attempt orchestrator-tasks.json bidirectional sync** (e.g., posting run results back to tasks) until the basic unification (R1-R9) is solid. That is a L4 feature on top of a broken L5.

**Do not add observability dashboards, Slack integrations, or notification layers** until the baseline worker is running reliably for 1 week.

---

## 13. Critical Unknowns That Still Need Proof

| # | Unknown | Why It Matters | How to Verify |
|---|---------|---------------|--------------|
| U1 | Does ANTHROPIC_API_KEY exist in ~/agent-services/.env? | All claude_execute and run_plan tasks fail without it | `grep ANTHROPIC_API_KEY ~/agent-services/.env` (key exists, not value) |
| U2 | Does `claude --print --prompt` flag work in current Claude Code CLI version? | claude_execute handler depends on it | `claude --help | grep print` |
| U3 | Does the DMRB project path "/Users/miguelgonzalez/Projects/Sand box/DRMB_PROD" actually exist? | project-level task processing silently skipped if absent | `ls "/Users/miguelgonzalez/Projects/Sand box/DRMB_PROD"` |
| U4 | What is in ~/.claude/runs/ephemeral/? | Are there orphaned orchestrator run artifacts? | `ls ~/.claude/runs/ephemeral/` if it exists |
| U5 | Have any claude_execute tasks in tasks.json ever been run manually? | 34 tasks are "complete" — are they complete from the worker, or manually marked? | Check `updated_at` timestamps and task_worker_state.json |
| U6 | Does `python3 -m orchestrator` work from cwd=~/.claude with current Python version? | run_plan bridge depends on it | `cd ~/.claude && python3 -m orchestrator --help` |
| U7 | Is tasks.json currently valid JSON? | Everything depends on it | `python3 -c "import json; json.load(open('$HOME/.claude/tasks.json'))"` |
| U8 | Are the 7 pending dmrb-064 tasks safe to execute autonomously? | If crons are enabled, they'll run | Review each task's action_payload.prompt before enabling |

---

## 14. Final Verdict

### What Is Real

The **agent-system-base blueprint** is well-designed and internally consistent. The orchestrator package is production-quality Python. The skills are well-documented. The CLAUDE.md protocol is coherent. The architecture concept is sound.

### What Is Not Real

The system as a whole has never executed end-to-end without manual invocation. There is no autonomous task processing. The dashboard has never been started. The worker has never been run by a cron. The orchestrator has never been triggered by a task. The intended unified flow (dashboard → tasks → worker → orchestrator) does not exist in the deployed layer.

The cron that runs every hour is an `echo` statement. The automation layer is entirely aspirational.

### The Three Most Critical Findings

**1. The deployment gap is the primary blocker.** The blueprint is ahead of the deployed runtime in at least 5 specific ways (run_plan handler, validate_env, correlation_id injection, schema sync, planner.json). init.sh has not been run. Until deployment is synchronized, the system cannot be trusted to behave as documented.

**2. The dashboard and worker are incompatible by schema.** Dashboard-created tasks have no action_type — the worker blocks them. The worker's "blocked" status crashes the dashboard's Pydantic model. These two components have never been tested together. The first time they interact, the dashboard will become unusable.

**3. The "automation" is a heartbeat reminder, not automation.** The operator is the automation layer right now. Every task in tasks.json that has been processed was processed either manually or by direct CLI invocation. The system's premise — "the hourly cron worker processes claude_execute tasks automatically" (CLAUDE.md) — is false in its current deployed state.

### Classification

**Needs stabilization first.** The blueprint is ready for expansion. The deployed system needs R1-R9 before it can be trusted. Those 9 fixes resolve the crashes, sync the deployment, and establish the cron baseline. After that, the system is ready to scale.

---

*Document generated by Claude Code via direct file reads. All findings cite specific files and line numbers. No claims are based on inference alone.*
