# UI Specialist — proposal contract

## Canonical structure

`Shared documents/auxiliary-agents/proposal_schema.md` + `Shared documents/auxiliary-agents/enforcement_rules.md`.

## Title line

`# Proposal — UI Specialist — [YYYY-MM-DD]`

## Section emphasis

| Section | UI Specialist focus |
|---------|---------------------|
| **Scope** | Screens, journeys, personas slice; exclusions. |
| **Decisions** | UX tensions (density vs clarity, optimistic vs confirmed, etc.). |
| **Options (A/B/C)** | Flow or state-machine postures; suggested default for Architect. |
| **Constraints** | Design system, platform, offline/latency from user/Architect. |
| **Risks** | Confusing states, race UX, a11y debt. |
| **Invariants** | Candidate UX truths (e.g. “destructive acts confirm”) — “Candidate:”. |
| **System Impact** | Surfaces/components **may** touch — declarative. |
| **Open Questions** | Unknown user cohort, missing design system, unclear errors from API. |

## Extra invalid patterns (UI Specialist)

- Pixel-perfect specs presented as requirements without Architect.
- Procedural “QA steps” or test cases (use declarative **Observable signal** language in **Risks**/**Open Questions** only).
