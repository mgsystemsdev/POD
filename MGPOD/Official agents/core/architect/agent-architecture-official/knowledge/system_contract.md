# System contract

## Pipeline

**Architect** → `project.md` + `schema.json` → **Execution Spec Gate** → `tasks.json` → **Operator** → **Execution** → **Verification** (evidence vs contract).

## Persistence layer

Architect writes canonical artifacts directly to the POD dashboard via ChatGPT Actions:
- `project.md` (Section A + B) → blueprint `type: "prd"`
- `schema.json` → blueprint `type: "schema"`
- Architecture decisions → `/api/projects/{id}/decisions`
- Project-scope KV (e.g. `current_prd_blueprint_id`) → `/api/projects/{id}/memory/{key}`

Downstream agents (Spec Gate, Operator) read blueprints from the same store. The `blueprint_id` is the handoff reference — not a file path. See `persistence_contract.md` for call order, version discipline, and error handling.

## Artifact paths

| Artifact | Path |
|----------|------|
| `project.md` | `[project-root]/.claude/context/project.md` |
| `schema.json` | `[project-root]/.claude/context/schema.json` |

Do **not** use legacy `.claude/project.md` without `context/`.

## Section A

Full PRD: identity, requirements (full contracts), data model, workflows, architecture-as-spec, technical rules, file layout, MVP, risks, open items. **Source of truth** for conflicts and updates.

## Section B — strict schema (10 sections, fixed order)

**Exact** headings below; **this order only**. Every section has content; if N/A: `N/A — [reason]`.

```markdown
## Project Name
## System Type
## Architecture
## Critical Constraints
## MVP Scope
## Out of Scope
## Requirements
## File Structure
## Current State
## Next Scope
```

### Per-section intent

| Section | Content |
|---------|---------|
| Project Name | Name |
| System Type | One sentence: kind of system |
| Architecture | Stack, layers, components, how they connect (2–5 sentences) |
| Critical Constraints | 3–7 hard rules: forbidden patterns, security, data, performance floors |
| MVP Scope | Bullets: v1 |
| Out of Scope | Bullets: deferred |
| Requirements | Each REQ-ID: Trigger, Input, Output, Constraints, Failure path, then `Done when:` |
| File Structure | Compact tree: key dirs/files |
| Current State | What exists in repo/product today |
| Next Scope | Immediate work after this PRD |

### Requirements block

- Stable unique REQ-IDs (e.g. `REQ-001`).
- Five elements + Done when per [requirement_contract.md](requirement_contract.md).

## Baton rules

1. **Section B** is the **machine baton** to Execution Spec Gate: paste **entire** Section B (`## Project Name` through `## Next Scope`) as the Gate opening payload.
2. **Section A** must be **saved** before handoff; never treat Section B as standalone source of truth without Section A on disk.
3. Regenerate Section B whenever Section A changes.
4. Gate + Operator consume Section B for context; execution consumes **task** objects from `tasks.json` ([task_spec.md](task_spec.md)).

## Handoff rules

1. User saves **full** `project.md` (Section A + Section B) to `.claude/context/project.md` and `schema.json` alongside.
2. **Execution Spec Gate** first message: full Section B + one line: new project vs scope addition vs PRD update (as Architect states).
3. **Operator** session: paste Section B per operator doc.
4. **Traceability:** every task in `tasks.json` maps to **exactly one** `requirement_ref` (REQ-ID). No task without REQ; no orphan REQ in MVP without eventual task path in Section A narrative.

## Architect session modes

| Mode | Start condition |
|------|-----------------|
| New | No PRD |
| PRD update | User pastes Section A or full file; delta |
| Scope addition | User pastes Section B + describes addition; merge + conflict check |

## Key terms

| Term | Definition |
|------|-----------|
| **Requirement** | A five-element testable contract (Trigger, Input, Output, Constraints, Failure path) that passes the contract test. Authored only by Architect. If it cannot be tested — it is a wish, not a requirement. |
| **Proposal** | Advisory input from an auxiliary agent (`proposal_[YYYYMMDD]_[agent-role].md`). Non-authoritative. Architect alone promotes proposal content into Section A / Section B / `schema.json`. |
| **Decision** | An architectural or strategic choice logged to `decisions.md` by the pipeline Strategist (GPT-3). Authoritative once logged; affects task validity (drift detection). |
| **Contract** | Shorthand for "requirement contract" — the five-element structure that every requirement must satisfy before entering the PRD. |
| **Task** | A `tasks.json` entry produced by Spec Gate. Maps 1:1 to a single REQ-ID. The execution unit consumed by Operator and Claude Code. |
| **Handoff** | A baton document passed between pipeline stages: `project.md` (Architect → Spec Gate / Operator), `tasks.json` (Spec Gate → Operator), `session.md` (Operator → Operator), `decisions.md` (Strategist → Operator / Architect). |
