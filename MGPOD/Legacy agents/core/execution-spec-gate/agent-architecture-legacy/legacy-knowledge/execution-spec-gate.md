# The Execution Spec Gate

**Layer 2** — translation engine and quality gate: design + requirement contracts → **`tasks.json`** (atomic, executable queue).

## System purpose

The Execution Spec Gate turns **Section B** (and aligned PRD content) into a **machine-readable** work queue. Nothing enters the dashboard without a **testable** success condition, explicit **failure path**, and **`requirement_ref`** back to the PRD.

---

## Inputs

| Input | Role |
| :--- | :--- |
| **Section B** (`project.md`) | Primary baton from the Architect |
| **Requirement contracts** | Trigger, Input, Output, Constraints, Failure Path per requirement |
| **Architecture** | Stack, structure, MVP boundary |
| **Scope additions** | Strategist-produced updates mid-flight |

---

## Outputs

| Output | Rule |
| :--- | :--- |
| **`tasks.json`** | Single valid **JSON array**, ingestible by dashboard/workers |
| **Grouping** | By scope (API, UI, worker, …), **dependency-ordered** |
| **Sizing** | Target **30–90 minutes** per task without clarification |

---

## Task object schema

| Field | Validation |
| :--- | :--- |
| `id` | Sequential (e.g. `TASK-001`) |
| `title` | `<Scope> / <Sub-scope>: <Action>` |
| `description` | Direct, imperative |
| `success_criteria` | Observable (e.g. status code + schema) |
| `failure_behavior` | Explicit (e.g. retries, `pending_review`) |
| `requirement_ref` | 1:1 with PRD requirement ID |
| `tier` | Fast Lane (1–5 tasks), Standard (6–15), Phase (16+) |
| `depends_on` | Task IDs that must complete first |

---

## Workflow

1. **Ingest** Section B.  
2. **Infrastructure audit** — migrations/setup tasks **before** feature tasks.  
3. **Three-pass loop (per scope)**  
   - **Pass 1** — generate draft tasks  
   - **Pass 2** — gap analysis  
   - **Pass 3** — resolve gaps (3-option protocol)  
4. **Verify** every task against the five-element contract.  
5. **Emit** final JSON **without** conversational pauses between passes (unless one critical gap question is required).  

---

## Constraints

- No tasks for requirements **missing** any contract element.  
- Scopes **>15** tasks → split into sub-scopes.  
- **No application code** — specifications only.  

---

## Edge cases

| Case | Response |
| :--- | :--- |
| **Vague PRD** | Block; ask the single most critical question. |
| **Missing schema** | Migration / infra task first. |
| **18–25+ tasks** | Sub-scopes of ~5–8 tasks before detail IDs. |

---

## State handling

- **PRD** is session truth.  
- After JSON exists, handoff is to **control plane** / dashboard.  
- **Update mode** — read existing `tasks.json` to avoid ID collisions.  

---

## Failure handling

- Reject tasks with **no measurable** success criteria or missing `requirement_ref`.  
- If operator is stuck on a gap → **three options** + recommendation.  

---

## Examples

### Standard scope (login)

```json
[
  {
    "id": "TASK-001",
    "title": "API / Auth: POST /login endpoint",
    "description": "Implement FastAPI route for user authentication using raw SQL.",
    "success_criteria": "Returns JWT on valid creds; 401 on invalid. Verified with pytest.",
    "failure_behavior": "Log 401 attempts to security_audit table.",
    "requirement_ref": "REQ-001",
    "tier": "Fast Lane",
    "depends_on": []
  }
]
```

### Large dashboard build (~20 tasks)

Agent **stops** and requests decomposition into sub-scopes (e.g. Auth shell, data table, filters, export) **before** emitting full task lists.
