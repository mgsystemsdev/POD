# Agent Evaluation: Access, Boundaries, and Ownership

This document establishes the structured evaluation of core agents, defining their access levels, operational boundaries, and resource ownership to ensure a distributed and secure multi-agent system.

## 1. Access Control Matrix

| Agent Category | Representative Agents | Read Scope (DB & System) | Write Scope (DB & System) | Tool Permissions |
| :--- | :--- | :--- | :--- | :--- |
| **Architect** | `senior_dev_guide` | Full (All tables, Code, Docs) | `blueprints`, `decisions`, `memory` | Read-only Tools |
| **Planner** | `planner` | `tasks`, `projects`, `blueprints` | `proposed_actions` (tasks), `blueprints` | Read-only Tools |
| **Construction** | `create`, `skill-creator`, `seed-project` | `tasks`, `blueprints`, `memory`, Code | Filesystem, `proposed_actions` | Write-capable Tools |
| **Integration** | `merge` | All agent outputs, Filesystem | Filesystem, `proposed_actions` | Write-capable Tools |
| **Auxiliary** | `devil-advocate`, `security-reviewer`, `deep-debugger`, `drift-detector` | Upstream outputs, scoped Code | `auxiliary_agent_outputs` | Read-only Tools |
| **Intelligence** | `context`, `research`, `intent_router` | Codebase, Docs, Web | None (Temporary logs only) | Read-only + Web |

---

## 2. Boundaries and Permissions

### General Policies
- **Default Policy**: Deny all write access unless explicitly granted.
- **Project Isolation**: Agents must not interact with resources outside the current `project_id`.
- **Human-in-the-Loop (HITL)**: No direct mutation of `tasks` or `files` (production) without staged `proposed_actions` or explicit `merge` steps.

### Detailed Boundaries
- **Architect**: Can define the "What" and "How" via blueprints but never performs the "Do" (code changes).
- **Auxiliary Agents**: Strictly confined to the `auxiliary_agent_outputs` table. They provide feedback but do not issue commands.
- **Planner**: Cannot modify code. Can only propose work units (tasks).
- **Construction Agents**: Cannot change architectural decisions or blueprints. They must flag "Architectural Tension" if they find a conflict.

---

## 3. Resource Ownership Map

| Resource | Ownership Type | Description | Primary Writer(s) |
| :--- | :--- | :--- | :--- |
| **`blueprints`** | **Shared (Controlled)** | System design and implementation plans. | Architect, Planner |
| **`decisions`** | **Shared (Restricted)** | Immutable record of architectural choices. | Architect |
| **`auxiliary_agent_outputs`**| **Shared (Append-only)**| Specialized reviews and feedback. | All Auxiliary Agents |
| **`proposed_actions`** | **System Queue** | Staging area for tasks and mutations. | Construction, Planner, Merge |
| **`tasks`** | **System Core** | The authoritative work queue. | Approved Proposals only |
| **`memory`** | **Shared KB** | Key-value store for patterns and facts. | Architect, Construction |
| **`files`** | **Project Artifact** | Source code and configuration files. | Create, Merge, Skill-creator |

---

## 4. Dependency Mapping

### Sequential Flow (The Execution Pipeline)
1. **`intent_router`** (Input: Goal) -> Proposes Agent Chain.
2. **`context` / `research`** -> Provides factual foundation.
3. **`planner`** (Input: Research + Blueprint) -> Decomposes into Tasks.
4. **`create`** (Input: Tasks + Blueprint) -> Generates Code/Artifacts.
5. **`Auxiliary Agents`** (Input: `create` output) -> Generates Reviews in `auxiliary_agent_outputs`.
6. **`merge`** (Input: `create` output + Reviews) -> Resolves conflicts and produces final `proposed_actions`.

### Strategic Flow (The Governance Loop)
- **`senior_dev_guide` (Architect)** -> Continuously monitors `tasks` and `runs`.
- **`system_base_manager`** -> Audits system health and drift against `blueprints`.

---

## 5. Evaluation Matrix (Agent Profiles)

| Agent | Reads | Writes | Shared Resources | Private Resources | Depends On | Supports |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Architect** | All | `blueprints`, `decisions` | `memory`, `blueprints` | None | All Logs | All Agents |
| **Planner** | `tasks`, `blueprints` | `proposed_actions` | `blueprints` | `plan_state.json` | `research` | `create` |
| **Create** | `blueprints`, Code | Files, `proposed_actions`| Codebase | `draft_artifacts` | `planner` | `merge`, `auxiliary` |
| **Auxiliary**| `create` outputs | `auxiliary_outputs` | `auxiliary_outputs` | None | `create` | `merge` |
| **Merge** | All outputs | Files, `proposed_actions`| Codebase | `conflict_log` | `auxiliary` | Human Operator |

---

## 6. Validation Criteria

- [x] All access is explicitly defined.
- [x] No unauthorized resource interaction (e.g., Auxiliary agents writing to `tasks`).
- [x] Ownership is unambiguous (e.g., Architect owns `decisions`).
- [x] Dependencies are necessary and non-redundant.
- [x] Boundaries enforce least-privilege principles.
