# AGENTS.md — Multi-Agent Coordination Rules

This file governs how agents coordinate in multi-agent mode and in orchestrator plans.
Claude reads this in multi-agent sessions.

---

## Agent Roster and Responsibilities

| Agent | Role | Can Write Files? | Critical? |
|-------|------|-----------------|-----------|
| `context` | Fetch docs, read codebase, gather external context | No | No |
| `research` | Cross-source research, synthesis, recommendations | No | No |
| `create` | Code generation, file creation, scaffolding | Yes | Yes |
| `merge` | Combine agent outputs, detect conflicts, produce final artifact | Yes | Yes |
| `intent_router` | Classify intent, propose agent chain, write tasks | No | No |
| `planner` | Decompose goals into tasks, write to tasks.json | Yes (tasks.json only) | No |
| `senior_dev_guide` | Code review, architecture guidance, sequencing | No | No |
| `workflow_coach` | QA, UX polish, gap detection | No | No |
| `skill-creator` | Skill authoring, evaluation, optimization | Yes | No |
| `system_base_manager` | System audits, health checks, drift detection | No | No |
| `seed-project` | Project seeding via init.sh | Yes | No |

---

## Output Format

Every agent step in an orchestrator plan MUST emit a valid `agent_output_v2` envelope:

```json
{
  "agent": "agent-name",
  "step_id": "step-identifier",
  "status": "success | failure",
  "output": {
    "summary": "one sentence",
    "artifacts": [],
    "recommendations": [],
    "tasks_to_create": []
  },
  "metadata": {
    "tokens_used": 0,
    "duration_ms": 0,
    "correlation_id": "uuid4"
  }
}
```

The `tasks_to_create` array is optional. If present, the merge step will write those tasks to `~/.claude/tasks.json` after the plan completes.

---

## Tool Permissions by Agent

**Read-only agents** (context, research, intent_router, senior_dev_guide, workflow_coach, system_base_manager):
- Allowed: Read, Grep, Glob, WebSearch, WebFetch
- Prohibited: Write, Edit, Bash (destructive commands)

**Write-capable agents** (create, merge, planner, skill-creator, seed-project):
- Allowed: Read, Write, Edit, Grep, Glob, Bash
- Must not write outside the declared project path

---

## Merge Conflict Resolution

When the merge agent detects conflicts between agent outputs:
1. **Artifact collision** (two agents created the same file differently) → flag both versions, do not auto-resolve
2. **Decision tension** (agents recommend contradictory approaches) → surface both in `merged.json`, let the human decide
3. **Output divergence** (factual disagreement) → flag the discrepancy with both source citations

Merge never silently discards an agent's output.

---

## Step Failure Handling

If an agent step fails:
1. Emit a `failure_envelope_v2` with the error reason
2. Mark step status `failed` in `run_state.json`
3. If the agent is `critical: true` → abort the plan, do not continue to dependent steps
4. If the agent is `critical: false` → continue the plan, pass failure context to dependent steps

The orchestrator will attempt one retry before emitting the failure envelope.

---

## Dependency Rules

- An agent must not start until all its `depends_on` steps are in `complete` or `skipped` status
- Circular dependencies are rejected at plan load time
- If a depended-on step failed but was non-critical, the dependent step receives the failure context in its input

---

## Task Proposal Protocol

AI agents must NEVER write tasks directly to tasks.json or to the SQLite tasks table.

When a step produces tasks to create, include them in `output.tasks_to_create` in the
`agent_output_v2` envelope. The worker or merge step calls
`proposed_action_service.propose("create_task", payload)` to stage them.

A human reviews and approves via `POST /api/proposed-actions/{id}/approve` in the dashboard.
Only then does `proposed_action_service.approve()` call `task_service.create_task()`.

Approved actions are auditable in the `proposed_actions` table (never deleted).

---

## Context Passing

Each agent receives:
- `context_for_<agent>.json` — summarized outputs from upstream steps
- `run_state.json` — current plan execution state
- `correlation_id` — traces this execution across tasks, plans, and logs

Write `context_for_<next_agent>.json` when your step has output that downstream agents need.
