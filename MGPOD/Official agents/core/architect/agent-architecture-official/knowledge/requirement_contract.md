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

1. **Output** — No “works,” “handles,” “supports.” Observable statements only.
2. **Input** — Always include invalid cases and system response.
3. **Failure path** — No “log and continue” without **where**, **what**, and **effect**.
4. **Constraints** — Numbers or explicit caps; unknown → **ASK**, not “reasonable performance.”
5. **Trigger** — Missing trigger → requirement has no entry point → **BLOCK** until defined.

## Done when (per REQ)

Immediately after the five elements, one line:

`Done when: [objective, testable condition tied to Output]`

Maps to `success_criteria` in tasks; verification must prove this line.

## Contract validation test (before REQ enters PRD)

Pass **only** if all are **yes**:

| Test | Question |
|------|----------|
| T1 | Can I **fire the Trigger** with **valid Input** and verify **Output** matches spec? |
| T2 | Can I **fire with invalid Input** and verify **Failure path**? |
| T3 | Can I verify **Constraints** (or is N/A with explicit reason in Section A)? |

If **no** → identify missing element → **ASK** one question (or **GUIDE** if stuck). **Do not** add the REQ.

## Anti-pattern vs pattern

**BAD:** “Users can log in.”

**GOOD:** Trigger: POST /login. Input: email (format), password (non-empty); invalid: malformed email → 422; wrong creds → 401. Output: 200 + JWT fields defined. Constraints: rate N/min per IP. Failure path: after 5 failures, lock flag + audit row + 429 with envelope.

Done when: automated test proves 200+JWT valid; 401 invalid; lock+audit after 5 failures.
