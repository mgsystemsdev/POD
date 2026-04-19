# System Design Agent — proposal contract

## Canonical structure

`Shared documents/auxiliary-agents/proposal_schema.md` + `Shared documents/auxiliary-agents/enforcement_rules.md`.

## Title line

`# Proposal — System Design Agent — [YYYY-MM-DD]`

## Section emphasis

| Section | System Design focus |
|---------|---------------------|
| **Scope** | Subsystems, integrations in scope; explicit exclusions. |
| **Decisions** | Monolith vs services, sync vs async, data ownership at boundary. |
| **Options (A/B/C)** | Architecture postures; suggested default for Architect. |
| **Constraints** | Stack, hosting, compliance — user/Architect only. |
| **Risks** | Cascading failure, tight coupling, ops complexity. |
| **Invariants** | Candidate boundaries (“Candidate: service X does not call DB of Y”). |
| **System Impact** | Components and integrations **may** change — declarative. |
| **Open Questions** | Unknown SLAs, unclear trust boundaries. |

## Extra invalid patterns (System Design Agent)

- Diagrams or narratives that read like **implementation tasks**.
- “Production architecture approved” language.
