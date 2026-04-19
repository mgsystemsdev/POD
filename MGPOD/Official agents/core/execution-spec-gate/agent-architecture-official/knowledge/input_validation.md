# Input validation (Section B)

## Authority

Section B format and section list: `Official agents/core/architect/agent-architecture-official/knowledge/system_contract.md` (locked ten headings, fixed order).

## Required structure

Input MUST be **entire Section B** from `## Project Name` through `## Next Scope`, as Markdown.

### Ten sections (strict)

Presence, **exact heading text**, and **non-empty body** required for each:

1. `## Project Name`
2. `## System Type`
3. `## Architecture`
4. `## Critical Constraints`
5. `## MVP Scope`
6. `## Out of Scope`
7. `## Requirements`
8. `## File Structure`
9. `## Current State`
10. `## Next Scope`

**Allowed exception:** If a section is genuinely N/A, body MUST be exactly one line: `N/A — [reason]`. Empty body = **REJECT**.

### Requirements block (per REQ)

Every `REQ-###` in `## Requirements` MUST contain **all** of:

| Element | Rule |
|--------|------|
| Trigger | Explicit entry condition (not implied) |
| Input | Valid cases + invalid cases + expected handling |
| Output | Observable; third-party verifiable |
| Constraints | Checkable limits or explicit N/A with reason |
| Failure path | Concrete: state, retries, notifications, blast radius — not “handle errors” |
| Done when | One line: `Done when: ...` testable and tied to Output |

Missing, vague (“works”, “supports”), or implied-only element → **BLOCK** (do not generate tasks).

## Reject conditions (hard stop)

- Wrong section count, wrong order, or wrong heading spelling vs `system_contract.md`.
- Any section body empty (and not the single-line N/A form).
- Any REQ missing Trigger, Input, Output, Constraints, Failure path, or `Done when:`.
- Input is Section A only / full `project.md` without Section B baton → **REJECT** with instruction: Section B only (per pipeline handoff).
- Ambiguous architecture or mutually exclusive stacks stated without resolution → **ASK** (see `gap_handling.md`), not generate.

## Pass criteria

All ten sections valid; every in-scope REQ passes contract test in `Official agents/core/architect/agent-architecture-official/knowledge/requirement_contract.md` (fire Trigger + valid Input → check Output; invalid Input → check Failure path; Constraints checkable or N/A).
