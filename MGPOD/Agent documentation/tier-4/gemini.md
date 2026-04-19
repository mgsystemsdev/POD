# Gemini

**Tier 4 — CLI agent** (Gemini CLI). **Fallback** and **context preprocessor** with a very large context window.

## System purpose

Gemini CLI is used when Claude Code’s **weekly budget** is exhausted or when the repo needs a **cold-open** map before execution. It can ingest a **large** slice of the tree in one pass and produce **baton files** (especially `analysis.md`) so expensive tools do not re-scan the same ground.

---

## Inputs

| Input | Role |
| :--- | :--- |
| **Global memory** (`~/.claude/memory/`) | Identity, preferences, standards, global decisions |
| **Project context** | `project.md`, `tasks.json`, `session.md` |
| **Baton** | `handoff.md`, `plan.md` from prior steps |
| **Repository** | Broad filesystem read for whole-repo analysis |

---

## Outputs

| Output | Description |
| :--- | :--- |
| **`analysis.md`** | Structure, components, flows, risks — seeds later sessions |
| **`handoff.md`** | Baton for the next tool without full re-read |
| **`session.md`** | Continuity — what was analyzed, what’s next |

---

## Key entities (conceptual)

| Entity | Role |
| :--- | :--- |
| **Project** | Root path + registered slug |
| **Blueprint** | Requirements/invariants from `project.md` |
| **Task** | Atomic work with `success_criteria`, `failure_behavior` |
| **Run** | Execution history row |

---

## Workflow (typical)

1. **Trigger** — budget hit or explicit “analyze first” need.  
2. **Ingestion** — read project files within model context limits.  
3. **Analysis** — compare disk to blueprint; note drift and risks.  
4. **Baton** — write `analysis.md` (and optionally refine `plan.md` / `handoff.md` / `session.md` per your pipeline).  

---

## Constraints

- Do not treat Gemini as a substitute for **session + PRD** reads when policy requires them.  
- **Vague requirements** → stop and ask; stale PRD → flag for Architect.  
- **Git** — no direct commits to `main`; use task branches via Operator discipline.  
- **Baton protocol** — don’t re-read sources already summarized in baton files.  

---

## Edge cases

| Case | Response |
| :--- | :--- |
| **Primary tool exhausted** | Gemini leads reasoning for multi-file work until budget recovers. |
| **Blueprint flaw found** | Block execution; document; PRD update via Architect. |
| **Scope creep** | Flag for Strategist / Spec Gate — don’t absorb silently. |

---

## State handling

- Authoritative context in `.claude/context/`; **`agents push`** mirrors to SQLite.  

---

## Failure handling

- **Loud diagnostics** — plain English stop + cause.  
- **RESET** — fundamental break → stop, document, return to Architect.  

---

## Examples

- **Budget exhausted** on TASK-015 (auth refactor) → `analysis.md` + `handoff.md` for Cursor / next tool + `session.md` update.  
- **Step 0 analysis** for project X → full-map `analysis.md` for downstream plan/build.  
