# Database Specialist — proposal contract

## Canonical structure

`Shared documents/auxiliary-agents/proposal_schema.md` + `Shared documents/auxiliary-agents/enforcement_rules.md`.

## Title line

`# Proposal — Database Specialist — [YYYY-MM-DD]`

## Section emphasis

| Section | Database Specialist focus |
|---------|---------------------------|
| **Scope** | Dataset, workloads, environments in scope. |
| **Decisions** | Index vs materialize, sharding, replication tensions. |
| **Options (A/B/C)** | Storage/index postures; suggested default for Architect. |
| **Constraints** | RPO/RTO, size limits — from user/Architect. |
| **Risks** | Lock escalation, vacuum/compact issues, migration cutover risk. |
| **Invariants** | Candidate DB truths (e.g. “no table scan on hot path”) — “Candidate:”. |
| **System Impact** | Stores, replicas, caches **may** be touched — declarative. |
| **Open Questions** | Access patterns unknown, engine TBD. |

## Extra invalid patterns (Database Specialist)

- Executable SQL migration sequences as tasks.
- Declaring final index list as “approved.”
