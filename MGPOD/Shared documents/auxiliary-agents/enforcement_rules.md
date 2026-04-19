# Auxiliary agents — enforcement rules

## Output gate (self-check before sending)

Reject your own output if any check fails; fix and resend.

1. **Structure:** All eight sections present with exact headings from `Shared documents/auxiliary-agents/proposal_schema.md`.
2. **Single artifact:** One proposal file body only (no side-channel “real” spec).
3. **No REQ/task language:** No REQ-IDs, no `Done when:`, no tasks.json, no “Step 1…” runbooks.
4. **No pipeline coupling:** No instructions to Spec Gate or Operator.
5. **No authority claims:** No “approved,” “signed off,” “final requirement,” “must ship as stated.”
6. **Conflicts:** If two options are incompatible, they appear as **separate options** or under **Risks** / **Decisions** — **not** merged.
7. **Stack:** Tech stack is **only** asserted when user or Architect artifacts provided it; otherwise **Open Questions** or **Constraints** (“Unknown until Architect defines stack”).

## Invalid output — recovery

If user asked for something that would violate rules (e.g. “write my REQ-IDs”):

1. Refuse the forbidden part briefly.
2. Provide the closest compliant alternative inside **Options** / **Open Questions** for Architect to formalize.

## Conflict with other specialists

When user indicates another specialist proposal disagrees:

- Name the conflict in **Decisions** and **Risks**.
- Keep **Options** comparable.
- **Do not** resolve by fiat; recommend **one** default for Architect with explicit assumptions.

## Cursor / Gemini as analysis engines

When tool output is incorporated:

- Summarize as **Options (A/B/C)** with tradeoffs.
- Label source as **analysis input**, not decision.
- **Suggested default** line remains **advisory**.

## Traceability

In the title line, include **agent role** and **date** so Architect can stack-rank multiple proposals.

## Agent-specific checks

Apply additional invalid patterns listed in the active agent’s `agents/<agent_id>/knowledge/failure_modes.md` and `proposal_contract.md`.
