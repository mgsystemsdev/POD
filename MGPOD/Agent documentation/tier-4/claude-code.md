# Claude Code

**Tier 4 — CLI agent.** Primary power tool — Layer 4 execution (agentic coding environment).

## System purpose

Claude Code turns **approved, requirement-backed tasks** into **committed, traceable** code for high-value, repo-scale work. It runs inside a **context-driven pipeline** where **files** (`.claude/context/`) are authored truth and the database is the operational mirror — reducing guessing and context loss.

---

## Inputs

| Input | Role |
| :--- | :--- |
| **Global memory** (`~/.claude/memory/`) | Identity (`user.md`), preferences, standards, global `decisions.md` |
| **Project context** (`.claude/context/`) | `project.md`, `tasks.json`, `session.md`, project `decisions.md`, baton files |
| **Tool adapters** | Thin `CLAUDE.md` → pointers into `.claude/context/` (no duplicate stacks) |
| **Codebase** | Local filesystem + terminal (tests, git, shell) |

---

## Outputs

| Output | Description |
| :--- | :--- |
| **Git artifacts** | Task branches (e.g. `feature/TASK-001`) |
| **Commits** | Changes mapped 1:1 to tasks; PR → merge workflow |
| **Continuity** | Updated `session.md` |
| **Decisions** | New `decisions.md` entries when architecture shifts |
| **Verification** | Objective evidence (logs, tests, screenshots) for the **done condition** |

---

## Key entities

### Task (summary)

| Facet | Fields / notes |
| :--- | :--- |
| **Identity** | `task_id`, `project_id` |
| **Definition** | Title (scope/sub-scope), description, status (`pending` / `in_progress` / `done` / `blocked`) |
| **Execution contract** | `requirement_ref`, `success_criteria`, `failure_behavior` |
| **Hierarchy** | Priority, tier (e.g. Fast Lane / Standard / Phase), `depends_on` |

### Other

- **Run** — execution attempt history (inputs, outputs, success/failure).  
- **Project blueprint** — versioned mirror of `project.md` in SQLite for the dashboard.  

---

## Workflow — task cycle (summary)

1. **Session start** — read `session.md` + `project.md`; no execution before context gate.  
2. **Task selection** — operator picks task from dashboard; task ID drives the branch name.  
3. **Git gate** — clean `main`, pull, create isolated task branch.  
4. **Step 0 analysis** — map files/connections before edits.  
5. **Plan mode** — research and propose approach (e.g. Shift+Tab).  
6. **Human approval** — operator approves `plan.md` before writes.  
7. **Implementation** — minimal, plan-aligned changes.  
8. **Self-verification** — tests/logs before “done.”  
9. **Evidence** — Operator collects objective proof vs success criteria.  
10. **Plain English** — what changed and risks (no code blocks in operator-facing translation).  
11. **Review / commit** — operator approves commit command.  
12. **PR** — push; open PR in GitHub UI.  
13. **Merge & pull** — merge on GitHub; delete branch; pull `main`.  
14. **Closeout** — `session.md` + `agents push` to sync SQLite.  

---

## Constraints

- **WIP = 1** — one task in progress.  
- **Source of truth** — author on disk; DB mirrors.  
- **No blind execution** — require project + session context.  
- **PR discipline** — no casual local merge to `main`; use GitHub PR for self-review.  
- **Plain English** — operator summaries without code fences where policy forbids them.  

---

## Edge cases

| Case | Response |
| :--- | :--- |
| **Budget exhaustion** | Fallback protocol — e.g. Gemini CLI / Cursor for scoped work. |
| **Design inconsistency** | Stop; document; Architect / PRD update. |
| **Verification fail** | Correction loop; no commit until contract satisfied. |
| **Scope creep** | Operator stops; new work → Spec Gate → new tasks. |

---

## State handling

- Authored state in `.claude/context/`; mirrored via `agents push`.  
- Use `/compact` when chat context is noisy.  
- Prefer **read session first** for fast resume (~2 min vs re-deriving context).  

---

## Failure handling

- **Loud failures** — name the step (`agents init`, `agents push`, etc.) + rollback hints.  
- **RESET** — foundation errors → stop, document, fix PRD/task list before retry.  
- **Diagnostics** — plain English root cause, not hidden stack-only errors.  

---

## Examples

- **TASK-012** (login + email validation) → branch, plan mode, tests for valid/invalid email, GitHub PR.  
- **Strategist prompt** (library X vs Y) → `decisions.md` + PRD stack update + dashboard sync.  
