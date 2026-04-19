# AGENTS.md — Multi-Agent Coordination Rules

This file governs how agents coordinate in multi-agent mode and in orchestrator plans.
Claude reads this in multi-agent sessions.

---

## Agent Roster and Responsibilities

Fields **`Critical?`** and **`Write/Edit?`** reflect `agents/<name>.json` as of this repo (`critical` defaults to **false** when omitted). **`review_wave`** is the plan in `agents/plans/review_wave.json`.

| Agent | Role (from agent JSON) | Write/Edit in tools_preferred? | Critical? | In `review_wave`? |
|-------|-------------------------|-------------------------------|-------------|-------------------|
| `context` | Resolve version-specific API and library behavior before coding. | No | **Yes** | No |
| `research` | Multi-source technical investigation with cited conclusions. | No | No | No |
| `create` | Produce reusable skills, prompts, or small automation artifacts. | Yes | No | No |
| `merge` | Consolidate parallel agent JSON outputs into one merged envelope. | Yes | **Yes** | **Yes** |
| `intent_router` | Classify intent and propose the right agent chain; does not execute. | No | No | No |
| `planner` | Decomposes goals into task lists for `~/.claude/tasks.json`. | Yes | No | No |
| `senior_dev_guide` | Guide sequencing; read project state; prevent drift. | No | No | No |
| `workflow_coach` | Extract friction into one controlled task; no code changes. | No | No | No |
| `skill-creator` | Skill lifecycle, evals, benchmarks, description tuning. | Yes | No | No |
| `system_base_manager` | Audit `~/.claude/` and agent-system-base; health and gaps. | Yes | No | No |
| `seed-project` | Seed a project via `init.sh`; confirm target dir first. | No (Bash, Read, Glob) | No | No |
| `devil-advocate` | Challenge solutions; counter-arguments and confidence scoring. | Yes | No | **Yes** |
| `security-reviewer` | Security pass with PASS / WARN / BLOCK. | Yes | No | **Yes** |
| `drift-detector` | Compare implementation to spec and decisions. | No | No | **Yes** |
| `deep-debugger` | Root-cause investigation; minimal fix proposals. | No (includes Bash) | No | No |
| `streamlit-designer` | Streamlit layout and code generation workflow. | Yes | No | No |

---

## Plan: `review_wave`

Steps (see `agents/plans/review_wave.json`): **devil-advocate**, **security-reviewer**, and **drift-detector** in parallel → **merge** (builtin) → `review_merged.json`. Plan description: mandatory hardening gate; a BLOCK from any agent cancels output and generates fix tasks.

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

Use each agent’s **`tools_preferred`** / **`tools_fallback`** in `agents/<name>.json` as the source of truth. The roster table’s **Write/Edit** column flags agents whose preferred tools include **`Write`** or **`Edit`**.

**No Write/Edit in preferred tools:** `context`, `research`, `intent_router`, `senior_dev_guide`, `workflow_coach`, `drift-detector`, `deep-debugger`, `seed-project` — several still include **Bash**, **WebSearch**, or **WebFetch**; see JSON.

**Write and/or Edit in preferred tools:** `create`, `merge`, `planner`, `skill-creator`, `system_base_manager`, `devil-advocate`, `security-reviewer`, `streamlit-designer`.

**Policy:** Must not write outside the declared project path unless the agent role explicitly targets global system files (e.g. `system_base_manager` audit outputs under `~/.claude/` per its notes).

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
