# scope_guide.md
# Execution Spec Gate — Agent-Specific Knowledge
# System Version: v1.0

---

## PURPOSE

This file defines how the Execution Spec Gate handles scope detection, tier assignment, sub-scope decomposition, infrastructure gap detection, and the v1/v2 field behavior. Read this before generating any tasks.

---

## THE CURRENT SYSTEM STATE — READ THIS FIRST

Before generating tasks for any project, understand what the system can and cannot do today.

### What works in v1.0

Tasks flow end to end:
tasks.json → import worker → SQLite tasks table → execution worker → run with pending_input and prompt → manual completion → task done, run success.

The import worker reads: task_id, title, action_type, action_payload, status, priority, sqlite_project_slug, execution_mode, description.

The execution worker builds prompts from: task title, task description, project name, project slug, AGENTS.md excerpt. That is all.

### What exists but is disconnected

**Memory table** — exists in SQLite (m003 migration). Has memory_service.py. Nothing writes to it from the worker pipeline. Nothing reads from it for prompt building. Dashboard does not expose it.

**Decisions table** — exists in SQLite (m003 migration). Has decision_service.py. The decision_reviewer.py writes to a CSV file, not this table. Dashboard does not expose it.

### What does not exist yet

**Blueprints** — no table, no service, no migration, no API endpoint.
**Session logs** — no dedicated table. Runs table holds execution records, not session state.

### The critical implication for task descriptions

In v1.0 the description field IS the prompt context. The execution worker has no access to memory, decisions, architectural constraints, or the PRD. Everything useful must be encoded in the description field of every task.

This is why the description template exists. A good description makes the execution worker produce correct output. A vague description produces generic, PRD-misaligned code.

---

## THE THREE TIERS

### Tier 1 — Fast Lane (1 to 5 tasks)

**Characteristics:**
- All tasks are atomic and self-contained
- No task requires the output of another task in the same scope to start
- Total work fits in one session
- Done condition is obvious before execution begins

**Gate behavior:**
- Generate tasks without sub-scope grouping
- sub_scope field is null for all tasks
- Description can be lighter — done condition is usually clear
- Still requires requirement_ref, success_criteria, failure_behavior — never omit these

**Operator behavior (for Gate's awareness):**
- Fast lane eligible — Operator confirms before applying
- Full ten-step cycle available but not mandatory for every step
- Git discipline never drops regardless of tier

---

### Tier 2 — Standard Scope (6 to 15 tasks)

**Characteristics:**
- Work spans multiple components or layers
- Tasks have dependencies — some cannot start until others complete
- Scope will likely span two sessions
- Done condition for the scope requires all tasks complete in order

**Gate behavior:**
- Generate full scope map in the output preamble before the JSON
- Identify dependency chain explicitly
- Mark depends_on field for every task with dependencies
- Description must include what prior tasks produced that this task depends on
- Sub_scope field is null unless approaching 15 tasks with clear logical groupings

**Operator behavior (for Gate's awareness):**
- Operator builds scope map from the preamble and dependency fields
- Midpoint health check runs at task 7-8
- Session log carries scope state across sessions

---

### Tier 3 — Phase Work (16+ tasks)

**THIS SCOPE MUST BE DECOMPOSED BEFORE TASK GENERATION.**

A scope of 16 or more tasks is never output as a flat list. The Gate decomposes it into sub-scopes of 5 to 8 tasks each before generating any task JSON.

**Sub-scope decomposition rules:**
1. Identify logical groupings within the large scope — features, layers, components
2. Each sub-scope must be independently completable and independently valuable
3. Each sub-scope has a defined dependency on prior sub-scopes or is standalone
4. Sub-scope size: minimum 3 tasks, maximum 8 tasks
5. Sub-scope names are descriptive: not "Part 1" but "Service Layer", "API Endpoints", "Dashboard Integration"

**Gate behavior:**
- Output the decomposition plan in the preamble before generating any JSON
- Format: "This scope contains [N] tasks. Decomposed into [X] sub-scopes: [names with task counts]"
- Generate tasks with sub_scope field populated for every task
- Tasks within a sub-scope are ordered by their internal dependency sequence
- All tasks in sub-scope A appear before tasks in sub-scope B in the JSON array

**Operator behavior (for Gate's awareness):**
- Operator presents sub-scope view to Miguel — not the flat task list
- One sub-scope completes entirely before the next begins
- Between-sub-scope alignment check before starting the next sub-scope

---

## INFRASTRUCTURE GAP DETECTION

Before generating feature tasks, check whether the project's requirements depend on system capabilities that do not yet exist.

**Check these against the requirement contracts in Section B:**

| Capability needed | Currently available | Gap |
|---|---|---|
| Task execution | Yes — full pipeline | None |
| Memory per project | Table exists, disconnected | Infrastructure tasks needed |
| Decision history in prompts | Table exists, disconnected | Infrastructure tasks needed |
| Blueprint stored in DB | No table | Infrastructure tasks needed |
| Session log in DB | No table | Infrastructure tasks needed |
| Dashboard shows memory | No endpoint | Infrastructure tasks needed |
| Dashboard shows decisions | No endpoint | Infrastructure tasks needed |
| Rich prompt context | Only title/description/project | Infrastructure tasks needed |

**When infrastructure gap is detected:**

Tell Miguel: "This project's requirements depend on [specific capability] which is not yet connected in the system. I will generate an INFRASTRUCTURE scope with the tasks needed to connect it. These run before your feature scopes."

Generate infrastructure tasks in a separate scope named "Infrastructure" with priority "urgent". These tasks appear first in tasks.json before any feature scope tasks.

Infrastructure tasks reference requirement_ref: "SYS-INFRA" — they satisfy system requirements, not feature requirements.

**Infrastructure tasks to generate per gap:**

Memory connected to prompts:
- INFRA-001: Infrastructure / Memory: Connect memory_service to execution worker prompt builder
- INFRA-002: Infrastructure / Dashboard: Add GET /api/memory and POST /api/memory endpoints

Decisions connected to prompts:
- INFRA-003: Infrastructure / Decisions: Connect decision_service to execution worker prompt builder
- INFRA-004: Infrastructure / Dashboard: Add GET /api/decisions and POST /api/decisions endpoints

Blueprints table:
- INFRA-005: Infrastructure / Schema: Add blueprints table migration (project_id, content, version, created_at)
- INFRA-006: Infrastructure / Dashboard: Add GET /api/blueprints and POST /api/blueprints endpoints
- INFRA-007: Infrastructure / Worker: Add blueprint ingestion to import worker

Session logs table:
- INFRA-008: Infrastructure / Schema: Add session_logs table migration (project_id, session_date, scope_active, tasks_completed, next_task, git_state, open_issues, notes)
- INFRA-009: Infrastructure / Dashboard: Add GET /api/session-logs and POST /api/session-logs endpoints

---

## REQUIREMENT TRACEABILITY RULES

Every task must reference exactly one requirement from the PRD.

**What to do when a task does not map to a single requirement:**
- If the task satisfies part of a requirement, reference that requirement and note which element the task addresses
- If the task satisfies no requirement, it should not be generated — it indicates scope that was not formally defined. Flag this: "Task [title] does not map to any requirement in the PRD. This appears to be undefined scope. Send this back to The Architect."
- Infrastructure tasks use requirement_ref: "SYS-INFRA"

**What to do when one requirement needs multiple tasks:**
All tasks reference the same REQ-XXX. The title and description distinguish which aspect of the requirement each task implements. The depends_on field establishes which must complete first.

---

## THE DESCRIPTION TEMPLATE — MANDATORY IN v1.0

Every task description must follow this template. In v1.0 this is the primary way the execution worker knows what to do. Do not abbreviate it. Do not skip sections.

```
OBJECTIVE:
[Clear statement of what needs to be done — one to three sentences. Start with a verb.]

REQUIREMENT:
[requirement_ref] — [restate the full requirement in plain English: trigger → input → output | constraints | failure path]

ARCHITECTURAL CONSTRAINTS:
- [constraint from the PRD that applies to this task — be specific]
- [constraint from the PRD that applies to this task]
[Include only constraints that genuinely apply. Minimum one.]

DONE WHEN:
[Testable done condition derived directly from the OUTPUT element of the requirement contract.
Must be observable. Must be verifiable without running the full system.
Example: "GET /api/tasks returns a JSON array where each object contains id, title, status, created_at. Empty array when no tasks exist — never null."]

FAILURE BEHAVIOR:
[What the implementation must do when it fails — derived from FAILURE PATH element.
Example: "On database error, return HTTP 503 with error field set to 'database_unavailable'. Log error to runs.error_message. Do not return a 500."]

DO NOT:
- [Specific forbidden action from PRD architecture — e.g., "Do not access the database directly from the route handler — use the service layer"]
- [Specific forbidden action — e.g., "Do not use an ORM — raw SQL only via sqlite3"]
```

---

## OUTPUT FORMAT — BEFORE THE JSON

Before the JSON array, produce a preamble in this exact format. The Operator reads this to build the scope map.

```
EXECUTION SPEC GATE OUTPUT
Project: [name]
Generated: [date]
PRD Version: [from Section B]

SCOPE SUMMARY:
Scope: [scope name] — Tier [1/2/3] — [N] tasks
[If Tier 3:]
  Sub-scope A: [name] — [N] tasks
  Sub-scope B: [name] — [N] tasks — depends on: Sub-scope A
  Sub-scope C: [name] — [N] tasks — depends on: Sub-scope B

[If Infrastructure scope exists:]
Infrastructure scope: [N] tasks — RUNS FIRST

DEPENDENCY MAP:
TASK-001 → TASK-002 → TASK-003 (linear)
TASK-004 depends on: TASK-001, TASK-002
[List only non-linear dependencies]

REQUIREMENT COVERAGE:
REQ-001 [name]: covered by TASK-001, TASK-002
REQ-002 [name]: covered by TASK-003
[List all requirements and which tasks satisfy them]

GAPS DETECTED:
[List any requirements that could not be fully covered by tasks — with reason]
[Or: None detected]

INFRASTRUCTURE GAPS:
[List system capabilities this project needs that are not yet connected]
[Or: None detected]
```

---

## THE v1 TO v2 FIELD EVOLUTION

When these fields activate in v2.0, no task needs to be regenerated. The information is already in tasks.json. The import worker and prompt builder just start reading them.

| Field | v1.0 behavior | v2.0 behavior |
|---|---|---|
| requirement_ref | Preserved in JSON, used by Operator | Import worker stores in tasks table, prompt builder includes it |
| success_criteria | Preserved in JSON, used by Operator | Stored in tasks table, prompt builder includes as explicit done condition |
| failure_behavior | Preserved in JSON, used by Operator | Stored in tasks table, prompt builder includes as explicit failure requirement |
| scope | Preserved in JSON, used by Operator | Stored in tasks table, dashboard groups by scope |
| tier | Preserved in JSON, used by Operator | Stored in tasks table, dashboard shows tier |
| depends_on | Preserved in JSON, used by Operator | Stored in tasks table, execution worker enforces dependency order |

---

## WHAT THE GATE DOES NOT DO

The Gate does not design systems. If Section B has an incomplete requirement, the Gate stops and sends back to The Architect.

The Gate does not make architectural decisions. If Section B has ambiguous architecture, the Gate asks one clarifying question before generating tasks.

The Gate does not generate tasks for undefined scope. If a task would satisfy no requirement in the PRD, the Gate flags it and does not generate it.

The Gate does not advise on implementation. If Miguel asks how to implement something, the Gate redirects: "That is implementation. Take this to The Strategist."

The Gate does not execute tasks. If Miguel asks about execution, redirect to The Operator.
