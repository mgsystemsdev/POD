# Schema Specialist — proposal contract

## Canonical structure

`Shared documents/auxiliary-agents/proposal_schema.md` + `Shared documents/auxiliary-agents/enforcement_rules.md`.

## Title line

`# Proposal — Schema Specialist — [YYYY-MM-DD]`

## Section emphasis

| Section | Schema Specialist focus |
|---------|-------------------------|
| **Scope** | Entities and relationships in scope; bounded context edges. |
| **Decisions** | Norm vs denorm, identity strategy, tenancy shape tensions. |
| **Options (A/B/C)** | Model postures; suggested default for Architect. |
| **Constraints** | Privacy, retention — from user/Architect. |
| **Risks** | Anomalies, orphan rows, dual-writes, ambiguous ownership. |
| **Invariants** | Candidate integrity rules — “Candidate:”. |
| **System Impact** | Entities **may** affect APIs, UI, reports — declarative. |
| **Open Questions** | Unknown engine, unclear lifecycle, Architect stack TBD. |

## Extra invalid patterns (Schema Specialist)

- DDL or migration scripts as execution steps.
- REQ-shaped “data shall…” blocks with REQ-IDs.
