# OpenCode

**Tier 4 — CLI agent.** **Automation layer** — only for **proven**, repeatable workflows.

## System purpose

OpenCode automates **validated** step sequences — typically after the same path was proven manually (often via Codex one-step-at-a-time). It reduces repetition once a pattern is **stable**; it is not for first-time or speculative work.

---

## Inputs

| Input | Role |
| :--- | :--- |
| **Validated plan** | Ordered steps that already worked manually |
| **Baton** | `analysis.md`, `plan.md` — full situational context |
| **Step paste** | Concrete sequence that passed manual proof |
| **Budget** | Separate from primary reasoning tools |

---

## Outputs

| Output | Description |
| :--- | :--- |
| **Repo changes** | Files touched in one automated pass |
| **Summary** | What changed and where |
| **`session.md`** | Automation run recorded for continuity |

---

## Key entities

| Concept | Definition |
| :--- | :--- |
| **Task** | Higher-level unit being automated |
| **Validated step** | **Action** + **context** (authorized files only) |
| **Implementation note** | In your stack, long-running automation may align with `task_worker.py` patterns — keep one mapping in code, one in docs. |

---

## Workflow — automation gate

1. **Manual proof** — operator/Codex completes steps once successfully.  
2. **Feed OpenCode** — paste or bind the validated sequence + baton context.  
3. **Autonomous run** — execute the full sequence in one pass.  
4. **Report** — files changed + summary.  
5. **Validate** — Codex or self-verification confirms requirements still met.  

---

## Constraints

- **Automation is earned** — never automate an unproven step.  
- **V1-before-V2** — manual proof at feature/task/system level before relying on OpenCode.  
- **WIP = 1** — still one active task context unless policy explicitly allows otherwise.  
- **No ad-hoc architecture** — implements defined plans, not new strategy.  

---

## Edge cases

| Case | Response |
| :--- | :--- |
| **Plan drift** | Repo changed since manual proof → stop; refresh analysis. |
| **Vague validated steps** | Pause; refine plan manually first. |

---

## State handling

- Consumes baton from Gemini/Codex/Claude so context **accumulates** without full re-reads.  
- **`agents push`** syncs results to SQLite for the dashboard.  

---

## Failure handling

- **Loud failure** — identify failing step + rollback guidance.  
- **Correction loop** — after failed automation, Operator issues fix prompt for manual path.  

---

## Examples

- **Paste 5 validated refactor steps** → OpenCode applies all; summary of touched files.  
- **“Automate this new idea”** with no proof → **blocked** until manual Codex (or equivalent) proof exists.  
