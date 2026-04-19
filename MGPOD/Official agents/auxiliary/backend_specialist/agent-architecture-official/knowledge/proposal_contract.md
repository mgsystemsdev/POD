# Backend Specialist — proposal contract

## Canonical structure

`Shared documents/auxiliary-agents/proposal_schema.md` + `Shared documents/auxiliary-agents/enforcement_rules.md`.

## Title line

`# Proposal — Backend Specialist — [YYYY-MM-DD]`

## Section emphasis

| Section | Backend Specialist focus |
|---------|---------------------------|
| **Scope** | Services, APIs, workflows in scope; out of scope integrations. |
| **Decisions** | REST vs RPC, sync vs async, idempotency, error model tensions. |
| **Options (A/B/C)** | Boundary and API posture; suggested default for Architect. |
| **Constraints** | Auth model hints, rate limits, compliance — from user/Architect only. |
| **Risks** | Cascading failures, ambiguous ownership, retry storms. |
| **Invariants** | Candidate API truths (e.g. “writes are idempotent under key K”) — “Candidate:”. |
| **System Impact** | Services, queues, caches **may** be touched — declarative. |
| **Open Questions** | Unknown SLOs, unclear auth, schema not frozen by Architect. |

## Extra invalid patterns (Backend Specialist)

- Normative OpenAPI titled “the contract” without Architect.
- Smuggling **Done when** or verification tasks into **System Impact**.
