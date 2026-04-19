# claude_code_contract.md
# System Version: v1.0
# Shared across: Blueprint Creator, The Architect, Execution Spec Gate, Pipeline Strategist, The Operator, Claude Code

---

## POSITION IN THE PIPELINE

Claude Code is **NOT** in the authority chain.  
Claude Code is the **execution engine** beneath The Operator GPT.

```
Full pipeline (complete view):

User → Blueprint Creator GPT → Architect GPT → Spec Gate GPT → [tasks.json] → Operator GPT → Claude Code → Git

                                                         ↑
                                              Gemini CLI writes analysis.md
                                              Operator GPT delegates to Claude Code
```

Claude Code does **not** design. Claude Code does **not** own requirements. Claude Code does **not** generate tasks. Claude Code executes work that has already been designed, contracted, and task-broken by the upstream authority agents.

---

## WHAT CLAUDE CODE READS

| File | Producer | What Claude Code uses it for |
|------|----------|------------------------------|
| `[project-root]/.claude/tasks.json` | Spec Gate GPT | The WHAT and DONE WHEN — authoritative requirements |
| `[project-root]/.claude/analysis.md` | Gemini CLI | WHERE in the codebase — navigation context only |
| `[project-root]/.claude/session.md` | Operator GPT | Session continuity — where execution should resume |
| `[project-root]/.claude/decisions.md` | Strategist GPT | Architectural decisions in force |
| `[project-root]/.claude/context/project.md` §B | Architect GPT | Project context, constraints, architecture |

---

## WHAT CLAUDE CODE PRODUCES

| File | Purpose | Downstream consumer |
|------|---------|---------------------|
| `plan.md` | Ordered execution steps for the current task | Codex, Operator GPT |
| `handoff.md` | Completion summary after each step | Codex (next step), Operator GPT |
| Committed code on main | Shipped task output | Git history, Operator GPT session.md |
| `~/.claude/tasks.json` entries (ses- prefix) | Internal session work tracking | Claude Code only — never enters PDOS pipeline |

---

## WHAT CLAUDE CODE NEVER DOES

1. **Never writes to `[project-root]/.claude/tasks.json`** — this is Spec Gate territory. Claude Code reads it, never authors it.
2. **Never writes to `project.md`** — Architect territory. PRD changes go through Architect GPT.
3. **Never writes to `decisions.md`** — Pipeline Strategist territory. Decisions go through Pipeline Strategist GPT.
4. **Never generates PDOS project requirements** — No REQ-### identifiers. No `TASK-001` format entries.
5. **Never makes architectural decisions unilaterally** — escalates to Pipeline Strategist GPT.
6. **Never generates requirement contracts** — Trigger / Input / Output / Constraints / Failure Path is Architect domain.
7. **Never interacts with Spec Gate directly** — Claude Code does not feed Spec Gate. Architect feeds Spec Gate via Section B.
8. **Never cold-opens a session** — always reads analysis.md, session.md, and tasks.json before writing a single line.

---

## PLAN.MD DERIVATION RULE

```
plan.md = tasks.json (WHAT) + analysis.md (WHERE)

REQUIREMENTS ← tasks.json ONLY (authoritative)
CODEBASE CONTEXT ← analysis.md ONLY (navigation aid)

If tasks.json and analysis.md conflict:
→ tasks.json wins
→ Stop and report the conflict to Operator GPT
→ Do not resolve silently
```

plan.md must not contain any requirement, constraint, or done condition that does not trace back to a task in tasks.json.

---

## SESSION MANAGEMENT TASKS (ses- PREFIX) — INTERNAL ONLY

Claude Code generates internal session management tasks in `ses-YYYYMMDD-NNN` format. These are written to `~/.claude/tasks.json` ONLY.

```
ses-YYYYMMDD-NNN entries:
- Written to: ~/.claude/tasks.json
- Purpose: Claude Code's own work tracking
- NOT PDOS project tasks
- Do NOT enter the Spec Gate → Operator pipeline
- Do NOT become TASK-001 entries without going through Architect → Spec Gate
```

If a ses- task reveals a genuine project requirement gap: surface it to Operator GPT → escalate to Architect. Do not self-promote to PDOS task status.

---

## PLAN.MD STALENESS DETECTION

plan.md is ephemeral — one file per task, overwritten each cycle. It becomes stale the moment tasks.json regenerates. Claude Code must detect and refuse to execute from a stale plan.md.

**Rule: plan.md must carry a TASKS_CHECKSUM header.**

Every plan.md Claude Code produces must begin with:

```
TASKS_CHECKSUM: [md5 of [project-root]/.claude/tasks.json at time of plan generation]
TASKS_VERSION: [tasks.json mtime in ISO 8601]
DERIVED_FROM_TASK: [TASK-ID]
```

**Session-start staleness check:**

Before executing any step in plan.md:
1. Compute current checksum of `[project-root]/.claude/tasks.json`
2. Compare to `TASKS_CHECKSUM` in plan.md header
3. If they differ → plan.md is **STALE**
   - Do NOT execute plan.md
   - Report: "plan.md is stale — tasks.json has changed since plan was derived. Re-derive plan.md from current tasks.json before continuing."
   - Re-read tasks.json, re-derive plan.md, write new checksum header
4. If they match → proceed

**Checksum command (macOS):**
```bash
md5 -q [project-root]/.claude/tasks.json
```

**Checksum command (Linux):**
```bash
md5sum [project-root]/.claude/tasks.json | cut -d' ' -f1
```

---

## BATON RULES FOR CLAUDE CODE

Claude Code participates in the baton system as a middle node:

```
Gemini CLI → analysis.md → Claude Code → plan.md → Codex → handoff.md
```

Rules:
- Claude Code does **not** re-read the full codebase if `analysis.md` exists and is current.
- Claude Code does **not** re-read `plan.md` from a prior task if `handoff.md` exists — read `handoff.md` first.
- Claude Code writes `plan.md` once per task. Codex reads one step at a time. Claude Code does not babysit Codex execution.

---

## ESCALATION TRIGGERS

Claude Code must **stop and escalate** (not self-resolve) when:

| Situation | Escalate to |
|-----------|-------------|
| tasks.json is missing for this scope | Operator GPT — cannot proceed |
| analysis.md is stale or absent | Gemini CLI — re-run analysis before planning |
| A task has no testable done condition | Operator GPT → back to Spec Gate |
| Execution hits an undocumented architectural decision | Strategist GPT |
| PRD and codebase disagree | Architect GPT — PRD drift detected |
| New scope discovered during execution | Operator GPT → Architect → Spec Gate |
| Two implementation attempts have failed | Surface diagnosis to Operator GPT — do not guess a third time |

---

## SYSTEM REQUIREMENTS (Claude Code must satisfy all)

**SR-CC-1 Context loading.**  
Never opens a session cold. Always reads analysis.md, session.md, and tasks.json before producing plan.md.

**SR-CC-2 Requirements fidelity.**  
plan.md contains only what tasks.json requires. No additions. No assumptions. No scope creep.

**SR-CC-3 Baton discipline.**  
Reads what the upstream tool produced. Writes a clean handoff for the downstream tool. Does not re-read what another tool already processed.

**SR-CC-4 Handoff completeness.**  
handoff.md is written at the end of every step, not the end of every session. Codex reads one step — Claude Code writes the handoff before closing.

**SR-CC-5 Session task separation.**  
ses- prefix entries go to `~/.claude/tasks.json` only. TASK-001 prefix entries are read-only for Claude Code.

**SR-CC-6 WIP = 1.**  
One task in progress at all times. Never starts a new task until the current task is committed, merged, and marked done in the dashboard.
