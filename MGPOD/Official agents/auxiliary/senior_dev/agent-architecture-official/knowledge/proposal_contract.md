# Senior Dev — proposal contract

## Canonical structure

`Shared documents/auxiliary-agents/proposal_schema.md` + `Shared documents/auxiliary-agents/enforcement_rules.md`.

## File naming

`proposal_[YYYYMMDD]_senior_dev.md` (date-stamped; never bare `proposal.md`).  
Same-day revision: `proposal_[YYYYMMDD]_senior_dev_v2.md`.

## Title and status block (mandatory)

Immediately after the heading, before any other content:

```
# Proposal — Senior Dev — [YYYY-MM-DD]

**Status:** PROPOSED
**Reviewed by Architect:** PENDING
**Outcome:** pending
```

Architect updates these three fields when processing the proposal.

## Section emphasis

| Section | Senior Dev focus |
|---------|------------------|
| **Scope** | Risk/review horizon; what is being challenged. |
| **Decisions** | Tradeoffs the team must own (speed vs safety). |
| **Options (A/B/C)** | Delivery/ops postures; suggested default for Architect. |
| **Constraints** | SLO hints, compliance, team skill — from user/Architect when known. |
| **Risks** | Operational, security, maintenance, unknown unknowns. |
| **Invariants** | Candidate prod truths (e.g. “break glass documented”) — “Candidate:”. |
| **System Impact** | Blast radius if proposal direction is wrong — declarative. |
| **Open Questions** | Missing metrics, ownership, observability — framed as questions, not tasks. Every question labeled **BLOCKING** or **NON-BLOCKING**. For BLOCKING questions, state what information would unblock Architect. Route repo questions as read-only discovery suggestions (NON-BLOCKING), not requests to the human. |

## Extra invalid patterns (Senior Dev)

- “Do these 5 steps before merge” checklists.
- REQ-shaped acceptance criteria.
- Staged execution plan as numbered steps (Stage 0–4) — reframe as Options (A/B/C) sequencing philosophy for Architect.
- Implementation Prompt packs or ordered prompt sequences — at most one read-only discovery suggestion in Open Questions.
- Validation as a second artifact — fold into Decisions / Risks / Options (advisory framing only).
