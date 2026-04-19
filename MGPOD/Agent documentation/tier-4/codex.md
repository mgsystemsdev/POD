# Codex

**Tier 4 — CLI agent.** Surgical **execution layer** — one approved plan step at a time.

## System purpose

Codex provides **controlled changes, no chaos**: it runs **individual, validated steps** from a pre-approved `plan.md`. It prioritizes **precision** and **minimal deviation** so implementation matches requirement contracts from the thinking phase — not open-ended design.

---

## Inputs

| Input | Role |
| :--- | :--- |
| **`plan.md`** | Ordered steps + **exact** files allowed to change |
| **`project.md`** | PRD — constraints and intent |
| **`analysis.md`** | Repo map / data flow — reduces ambiguity |
| **Budget** | Separate from Claude Code so execution can continue when reasoning budget is tight |

---

## Outputs

| Output | Description |
| :--- | :--- |
| **Surgical edits** | Minimal diffs only on plan-authorized paths |
| **`handoff.md`** | Per-step baton for the next tool (no full re-read) |
| **Evidence** | Logs/tests proving the **step** success criteria |

---

## Key entities

### Task step

Each step must specify:

- **`target_files`** — paths allowed to change  
- **`action`** — concrete change  
- **`validation`** — how success is proven  

### Handoff baton

- **`last_completed_step`** — position in `plan.md`  
- **`accumulated_context`** — summaries to avoid redundant scanning  

---

## Workflow — atomic execution loop

1. Load **exactly one** step from `plan.md`.  
2. Verify files exist and instructions are unambiguous.  
3. Execute with **minimal changes** — authorized files only.  
4. **Stop and ask** if anything is ambiguous (no guessing).  
5. Validate (tests/logs) for **this step only**.  
6. Update `handoff.md`.  
7. Repeat until the plan is complete.  

---

## Constraints

- **Never batch steps** in one turn.  
- **File isolation** — no edits outside the plan’s file list.  
- **Minimalism** — smallest edit that satisfies the step.  
- **Human gate** — commit only after verification + Operator review.  

---

## Edge cases

| Case | Response |
| :--- | :--- |
| **Vague step** | Block; 3-option clarification protocol. |
| **Regression elsewhere** | Stop; revert; escalate to Strategist. |
| **Stale `analysis.md`** | Stop; request fresh analysis if disk diverged. |

---

## State handling

- **Stateless** between tasks — position from `handoff.md` + `session.md`.  
- **Baton** — forward context without re-reading the whole repo.  

---

## Failure handling

- **Loud block** — explicit reason + copy-ready fix prompt.  
- **Correction loop** — diagnostic → revised instruction → retry step.  

---

## Examples

- **Step 3** — add `validate_email` to `utils.py` per plan → tests pass → `handoff.md` updated.  
- **Step touching `.env`** when not in plan → **blocked**; plan update required.  
