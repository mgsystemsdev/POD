# Requirement contract

## Definition

A **requirement** is a **testable contract**. If success and failure cannot be **observed**, it is not a requirement — it does not enter Section A.

## Five elements (all mandatory)

| Element | Must specify |
|--------|----------------|
| **Trigger** | Event, action, or condition that starts behavior (user action, API, cron, webhook, DB state, etc.). |
| **Input** | Data: fields, types, valid ranges/enums; **invalid** cases and expected rejection. |
| **Output** | Observable result: returned/stored/sent; format; **how a third party verifies success**. |
| **Constraints** | Limits: time, volume, dependencies, forbidden patterns, ordering — **checkable**. |
| **Failure path** | On error: retries (count, interval), persisted state, user-visible effect, blast radius. |

## Phrasing rules

1. **Output** — No "works," "handles," "supports." Observable statements only.
2. **Input** — Always include invalid cases and system response.
3. **Failure path** — No "log and continue" without **where**, **what**, and **effect**.
4. **Constraints** — Numbers or explicit caps; unknown → **ASK**, not "reasonable performance."
5. **Trigger** — Missing trigger → requirement has no entry point → **BLOCK** until defined.

## Done when (per REQ)

Immediately after the five elements, one line:

`Done when: [objective, testable condition tied to Output]`

Maps to `success_criteria` in tasks; verification must prove this line.

## Verification check (used by Operator in STEP 3)

When verifying a completed task, confirm all five elements were satisfied:
- Trigger: was the entry condition implemented correctly?
- Input: are valid and invalid inputs handled as specified?
- Output: does the observable result match the contract?
- Constraints: are all limits enforced?
- Failure path: does the failure behavior match the contract?

Never accept "it works" without evidence against these five elements.
