# Proposal File Schema (mandatory — all auxiliary agents)

## File naming convention (mandatory)

Proposals must use date-stamped filenames. Never use a bare `proposal.md`.

```
proposal_[YYYYMMDD]_[agent-role].md
```

Examples:
- `proposal_20260411_senior_dev.md`
- `proposal_20260411_database_specialist.md`
- `proposal_20260411_ui_specialist.md`

If the same agent produces a revised proposal on the same day:
```
proposal_20260411_senior_dev_v2.md
```

## Proposal lifecycle (mandatory)

Every proposal file must include a `## Status` line at the top, immediately after the heading:

```
# Proposal — [Agent Role] — [YYYY-MM-DD]

**Status:** PROPOSED | UNDER REVIEW | PROMOTED | REJECTED
**Reviewed by Architect:** [date, or PENDING]
**Outcome:** [promoted to Section A on [date] | rejected — reason | pending]
```

Architect updates the Status line when processing the proposal. This creates a simple audit trail without additional tooling.

Proposals are never deleted. A `REJECTED` or `PROMOTED` proposal stays in place as a record of what was considered.



Canonical shared contract. Per-agent fill guidance and extra invalid patterns: `Official agents/auxiliary/<role>/agent-architecture-official/knowledge/proposal_contract.md` (or `Official agents/core/strategist/agent-architecture-official/knowledge/proposal_contract.md` for the auxiliary Strategist).

## Validity rule

Output is **INVALID** if any section below is **missing**, **empty without justification**, or **renamed**.  
If a section is truly not applicable, write one line: `N/A — [reason]` (reason must be specific).

## Exact structure (headings must match character-for-character)

```markdown
# Proposal — [Agent Role] — [YYYY-MM-DD]

## Scope

## Decisions

## Options (A/B/C)

## Constraints

## Risks

## Invariants

## System Impact

## Open Questions
```

## Section intent

| Section | Content |
|---------|---------|
| **Scope** | What this proposal covers and explicitly excludes. Tie to user-stated work type (new / feature / refactor / exploration). |
| **Decisions** | Framing only: what must be chosen, tradeoffs, **tensions** (including conflicts with other specialists’ likely views). **Not** “we decided” as fact — use “Recommended for Architect: …” where needed. |
| **Options (A/B/C)** | Exactly three labeled options unless scope forces fewer; if fewer, state why and still label remaining options clearly. Each option: brief, comparable criteria. **End with one sentence:** “Suggested default for Architect consideration: [A|B|C] — because …” |
| **Constraints** | Hard limits: UX, legal, perf, compatibility, tech stack **as described by user or Architect artifacts** (do not invent stack as truth). |
| **Risks** | What goes wrong if wrong option is chosen; blast radius; unknowns. |
| **Invariants** | Properties that should **remain true** across implementations (candidate invariants for Architect to adopt or reject — **not** finalized system invariants). Prefix bullets with “Candidate:”. |
| **System Impact** | Which subsystems, data, APIs, UX surfaces **might** be touched; migration or rollback **considerations** — declarative, not a task list. |
| **Open Questions** | Everything still unknown; blocking vs non-blocking labeled. |

## Forbidden inside the proposal file

- REQ-IDs, `Done when:`, Spec Gate payloads, `tasks.json`, numbered “Step 1… Step 2…” execution instructions.
- Language implying Spec Gate or Operator **must** run next.
- Presenting auxiliary output as **final** product requirements.

## Procedural → declarative

If you catch yourself writing steps, convert to:

- **Intent:** what outcome must hold.
- **Constraint:** what must not happen.
- **Observable signal:** what would indicate success or failure (without writing verification tasks).
