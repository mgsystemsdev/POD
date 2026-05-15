# Input priority

## Priority tiers

| Tier | Sources | Weight | Role |
|------|---------|--------|------|
| **1 — Hard Authority** | Decisions, Approvals | Enforced unconditionally | Rules and permissions that cannot be overridden |
| **2 — Structural Truth** | Blueprints | Overrides Tiers 3–5 | Source of SR requirements; defines what the system is |
| **3 — Strategic Direction** | Strategist output | Informs FR intent | Tells the Architect what to build and why |
| **4 — Suggestions** | Agent Proposals | Lowest priority | Triggers new work; never overrides Tiers 1–3 |
| **5 — Soft Context** | Session Log | Reference only | Provides build state awareness; cannot influence contract fields |

## Conflict resolution

Higher tier always wins. Architect states the conflict before requesting resolution — never silently picks a side.

| Conflict | Action |
|----------|--------|
| Proposal conflicts with Blueprint | **BLOCK** + state conflict in one sentence + ASK once to resolve |
| Proposal conflicts with Decision | **BLOCK** + state decision that applies + reject proposal |
| Strategist direction conflicts with Blueprint | **BLOCK** + escalate; both parties must align before proceeding |
| Two Decisions conflict | **BLOCK** + surface both + require precedence decision |
| Session Log contradicts a Decision | Discard Session Log interpretation; enforce Decision |

## Usage rules

**Decisions and Approvals (Tier 1)**
- Applied to every contract, every turn
- No requirement proceeds if it violates a Decision

**Blueprints (Tier 2)**
- Source of all SR requirements
- If a proposal implies an architectural change not in the Blueprint → it becomes an FX or requires a Blueprint update first
- Architect reads Blueprint before processing any proposal

**Strategist (Tier 3)**
- Provides direction and "why" — Architect converts this into FR contracts
- Strategist cannot override architectural decisions in the Blueprint

**Agent Proposals (Tier 4)**
- Treated as raw input; classified into SR / FR / FX based on content
- A proposal that conflicts with a higher tier is rejected outright

**Session Log (Tier 5)**
- Used only to understand current build state (what is done, what is confirmed)
- Never used as the basis for contract fields
- If Session Log and a Decision conflict → Decision wins

## Input loading order

When starting a requirement cycle, read inputs in this order:

1. Decisions (Tier 1)
2. Approvals (Tier 1)
3. Blueprints (Tier 2)
4. Memory (cross-cutting context)
5. Backlog (current system state)
6. Strategist output (Tier 3)
7. Agent Proposals (Tier 4)
8. Session Log (Tier 5) — last; reference only
