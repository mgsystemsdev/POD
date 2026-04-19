# Kiro

**Tier 4 — CLI agent.** **Optimization / polish layer** — after a feature is built and verified.

## System purpose

Kiro does **non-logic-altering** cleanup, style polish, and **performance** tweaks once execution and verification have passed. It optimizes for **hygiene and speed**, not architectural redesign — keeping the repo maintainable without destabilizing core behavior.

---

## Inputs

| Input | Role |
| :--- | :--- |
| **Verified codebase** | Post–Claude/Cursor build + Operator verification |
| **`.claude/context/`** | `project.md` (intent), `MEMORY.md` (patterns) |
| **Directives** | e.g. “clean up,” “speed up,” “reduce complexity” |
| **Budget** | Separate optimization budget so polish doesn’t burn primary reasoning tokens |

---

## Outputs

| Output | Description |
| :--- | :--- |
| **Refactors** | Readability/complexity/speed **without** changing behavior |
| **Summary** | Files touched + what improved |
| **`decisions.md`** | If polish establishes a new standard worth recording |

---

## Key entities

### Optimization run (conceptual)

| Field | Use |
| :--- | :--- |
| **`run_type`** | e.g. `optimization` |
| **`parent_task_id`** | Feature task being polished |
| **`metrics`** | Optional before/after quality or performance signals |

### Skills (conceptual)

- **Code-review** — hotspots, style, complexity  
- **Security-audit** — patterns, duplication, risky structure  

---

## Workflow

1. **Trigger** — only after operator confirms feature **verified**.  
2. **Ingest** — map relevant modules and data flow.  
3. **Discover** — candidate cleanups (low risk first).  
4. **Surgical edits** — minimal diffs, authorized scope only.  
5. **Validate** — full test suite; **no** logic regression.  
6. **Closeout** — plain-English summary; commit/PR per Git rules.  

---

## Constraints

- **No core logic fixes here** — logic bugs go back to primary execution (Claude/Cursor + plan).  
- **Order** — after primary build completes.  
- **Minimal impact** — smallest change that meets the directive.  
- **Human gate** — merge via PR + review.  

---

## Edge cases

| Case | Response |
| :--- | :--- |
| **Speed vs readability** | Pause; operator chooses tradeoff. |
| **Regression** | Revert; flag Strategist. |
| **Stale PRD** | Block; Architect updates blueprint first. |

---

## State handling

- May read mirrored SQLite for visibility; **author** findings in `.claude/context/` first.  
- **`agents push`** locks continuity for the next session.  

---

## Failure handling

- **Loud diagnostics** — e.g. which step broke which test.  
- **Reversion** — if operator rejects polish, stash/revert branch before touching `main`.  

---

## Examples

- **ingest.py** loop cleanup → clearer names + extracted helpers; all ingestion tests still pass.  
- **Tasks API** latency → query/cache tweak; performance log; **unchanged** JSON contract.  
