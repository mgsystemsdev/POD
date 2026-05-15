# Requirement lifecycle

## State machine

| State | Who sets it | Entry condition | Exit condition |
|-------|-------------|-----------------|----------------|
| **DRAFT** | Architect | Requirement created — may have gaps | All 5 elements + type assigned |
| **VALIDATED** | Architect | All 5 elements + type present, T1/T2/T3 pass | Human/operator confirms |
| **APPROVED** | Human / Operator | Human reviews and confirms | Written to Backlog |
| **PROMOTED** | System | APPROVED and written to Backlog | Execution-Spec-Gate consumes |
| **EXECUTED** | Downstream agents | All tasks derived from this REQ complete | Verified against Done-When |
| **CLOSED** | Human / Operator | Verified — outcome matches Done-When | Terminal state |

## Architect controls only DRAFT and VALIDATED

Architect sets a requirement to DRAFT when creating it, and to VALIDATED when the contract is complete and passes all checks.

Architect does **not** approve, promote, execute, or close requirements.

## No state skipping

States must advance in order. Forbidden transitions:
- DRAFT → APPROVED (skip VALIDATED)
- DRAFT → PROMOTED (skip VALIDATED + APPROVED)
- VALIDATED → EXECUTED (skip APPROVED + PROMOTED)

Any attempt to skip a state → **BLOCK**.

## Write-trigger table

| Tab | Write when |
|-----|-----------|
| Requirements | Always — immediately after requirement reaches VALIDATED |
| Backlog | Only when status is APPROVED (never before) |
| Decisions | Only when a new system rule is introduced as part of a requirement |
| Memory | Only when a reusable pattern or constraint is discovered |
| Approvals | Only on explicit human confirmation (not inferred) |

## Failure handling rule

When an execution failure is reported:

1. **Do not modify** the original requirement — it stays in EXECUTED state
2. **Create a new FX** requirement at DRAFT state
3. The new FX must include:
   - `parent_requirement_id`: ID of the requirement whose execution failed
   - `failure_reason`: concrete description of what failed and why
   - `correction_scope`: what the fix must accomplish (no scope creep)
4. The new FX follows the full lifecycle from DRAFT

Original requirement history is preserved. The FX creates a traceable audit chain.

## Section ownership (shared tabs)

When Architect writes to a shared tab (Decisions, Memory, Approvals, Backlog):
- Locate and delete the existing **Architect section** in that tab
- Write the updated Architect section in its place
- Other agents' sections are untouched

Each agent owns exactly one named section per shared tab. Last write to that section is the source of truth for that agent.
