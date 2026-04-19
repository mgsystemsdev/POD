# PDOS full system evaluation and alignment plan

**Date:** 2026-04-11  
**Scope:** Read all documentation, detect conflicts, resolve them, enforce single system model  
**Source:** Captured from PDOS alignment working session (terminal plan output).

---

## Context

The PDOS (Personal Developer Operating System) is a multi-agent execution pipeline governed by a strict authority model. A full system evaluation was requested to find and fix all misalignments between:

- The **LOCKED CORE SYSTEM MODEL** (as specified in the evaluation prompt)
- The actual documentation across MGPOD, `~/.claude/CLAUDE.md`, and the agent infrastructure

Three parallel explore agents read all 114 MGPOD files, all `~/.claude/` config, and all `~/agents/` infrastructure. **Six conflicts** were confirmed.

---

## Confirmed conflicts

### CONFLICT 1 — tasks.json: two files, same name, contradictory rules

**Where:**

- `~/.claude/CLAUDE.md` § “Canonical Task File”: “One file. One source of truth. `~/.claude/tasks.json` ← ALL tasks, ALL projects. Never create or write to a project-local tasks.json.”
- `~/.claude/CLAUDE.md` § “Step 2 / Step 3”: “Preferred for project work: append to that repo’s tasks.json (project root)”
- `MGPOD/Shared documents/core-agents-contracts/system_contract.md`: “Producer: Execution Spec Gate. Location: `[project-root]/.claude/tasks.json`”

**Nature:** Direct self-contradiction within CLAUDE.md plus conflict with `system_contract.md`.

**Resolution:** There are two different files that both happen to be called `tasks.json`:

```
┌───────────────────────────────────┬─────────────────────────┬──────────────────────┬───────────────────────────────────┐
│               File                │        Producer         │        Schema        │              Purpose              │
├───────────────────────────────────┼─────────────────────────┼──────────────────────┼───────────────────────────────────┤
│ ~/.claude/tasks.json              │ Claude Code (session    │ ses-YYYYMMDD-NNN     │ Claude Code's internal session    │
│                                   │ tracking)               │ format               │ work tracking                     │
├───────────────────────────────────┼─────────────────────────┼──────────────────────┼───────────────────────────────────┤
│ [project-root]/.claude/tasks.json │ Spec Gate GPT only      │ TASK-001 format      │ PDOS project execution queue →    │
│                                   │                         │                      │ SQLite                            │
└───────────────────────────────────┴─────────────────────────┴──────────────────────┴───────────────────────────────────┘
```

These must **NEVER** be confused. The rule “Never write to project-local tasks.json” refers only to **Claude Code** not being allowed to write **PDOS** project tasks. The project-root `tasks.json` is **Spec Gate** territory exclusively.

---

### CONFLICT 2 — Claude Code role: “NOT a task generator” vs writes tasks at session start

**Where:**

- User’s **LOCKED SYSTEM MODEL**: “Claude Code is NOT: a source of truth, a requirement writer, a task generator, an authority layer”
- `~/.claude/CLAUDE.md` § “Session Start Step 2”: “Break the goal into 5–12 concrete subtasks… Write tasks to the task board” (Claude Code is instructed to generate and write task entries)

**Nature:** CLAUDE.md instructs Claude Code to generate tasks. The system model forbids Claude Code from being a PDOS task generator.

**Resolution:** Claude Code generates **SESSION MANAGEMENT TASKS** only (`ses-` prefix, internal to `~/.claude/tasks.json`). These are **not** PDOS project tasks (`TASK-` prefix, Spec Gate output). Claude Code never generates TASK-001 format entries. CLAUDE.md must be updated to make this distinction explicit and hard-enforced.

---

### CONFLICT 3 — plan.md derivation: “ONLY from tasks.json” vs “from analysis.md”

**Where:**

- User’s **LOCKED SYSTEM MODEL**: “Claude produces plan.md (derived ONLY from tasks.json)”
- `master-document.md` Layer 2 / Baton system: “analysis.md → Claude Code reads analysis.md (skips codebase) → Claude Code writes plan.md”

**Nature:** The master document requires `analysis.md` as a `plan.md` input. The system model says `tasks.json` is the only source.

**Resolution:** Both are correct in different senses:

- `tasks.json` provides **WHAT** to build and the **DONE WHEN** conditions — this is authoritative.
- `analysis.md` provides **WHERE** in the codebase — this is codebase navigation context only.

**Clarify:** `plan.md` **requirements** come exclusively from `tasks.json`. `analysis.md` is **context** for WHERE, not WHAT. This must be stated explicitly in the Claude Code contract document.

---

### CONFLICT 4 — the Canonical Task File self-contradiction in CLAUDE.md

**Where:** `~/.claude/CLAUDE.md` § “Canonical Task File” says two things that contradict each other:

1. `~/.claude/tasks.json` ← ALL tasks, ALL projects. Never create or write to a project-local tasks.json.
2. Three paragraphs later: “Preferred for project work: append to that repo’s tasks.json (project root)”

**Nature:** The rule and the preferred behavior contradict each other within the same section.

**Resolution:** Rewrite the section entirely. The “never write project-local tasks.json” rule means **Claude Code** never writes **PDOS** tasks there. The Spec Gate writes PDOS tasks to project-root `tasks.json`. Claude Code writes **SESSION** tasks to `~/.claude/tasks.json` only.

---

### CONFLICT 5 — missing explicit Claude Code positioning document in MGPOD

**Where:** MGPOD documents describe the four-GPT-agent pipeline and specialist agents thoroughly. No document explicitly defines Claude Code’s role in the pipeline or its relationship to the Operator GPT.

**Nature:** Gap, not conflict. The `system_contract.md` mentions Operator GPT delegates to execution tools but does not name Claude Code specifically or define its constraints.

**Resolution:** Create `MGPOD/Shared documents/core-agents-contracts/claude_code_contract.md` defining exactly what Claude Code is and is not allowed to do within the PDOS pipeline.

---

### CONFLICT 6 — session_contract vs CLAUDE.md on project-root `.claude/`

**Where:**

- `system_contract.md` § “Document Home”: “Every project has exactly one `.claude/` directory inside the project root” with `project.md`, `tasks.json`, `session.md`, `decisions.md`
- `~/.claude/CLAUDE.md` § “Canonical Task File”: “Never create or write to a project-local tasks.json”

**Nature:** The system contract says `tasks.json` lives in `[project-root]/.claude/tasks.json`. CLAUDE.md says never write project-local `tasks.json`.

**Resolution:** Spec Gate writes PDOS tasks to `[project-root]/.claude/tasks.json`. Claude Code **reads** this file (to build `plan.md`) but **never writes** to it. CLAUDE.md’s “never write” rule is specifically about Claude Code not being allowed to **WRITE** PDOS tasks — not a prohibition on the file’s existence.

---

## Documents to create / update

### 1. CREATE: `MGPOD/Shared documents/core-agents-contracts/claude_code_contract.md`

New file. Defines Claude Code’s exact role in the PDOS pipeline.

**Content to include:**

#### Claude Code in the PDOS Pipeline

**Position**

- Claude Code is **NOT** in the authority chain.
- Claude Code is the **EXECUTION ENGINE** beneath the Operator GPT.

**Pipeline (complete):** User → Architect GPT → Spec Gate GPT → Operator GPT → Claude Code

**What Claude Code READS**

- `tasks.json` (Spec Gate output) — the WHAT and DONE WHEN
- `analysis.md` (Gemini output) — WHERE in the codebase
- `session.md` (Operator GPT output) — session continuity
- `decisions.md` — architectural decisions in force

**What Claude Code PRODUCES**

- `plan.md` — derived from `tasks.json` (requirements) + `analysis.md` (codebase context)
- Committed code changes
- `handoff.md` (for Codex handoff)

**What Claude Code NEVER DOES**

- Never writes to `[project-root]/.claude/tasks.json` (Spec Gate territory)
- Never writes to `project.md` (Architect territory)
- Never writes to `decisions.md` (Strategist territory)
- Never generates PDOS project requirements (TASK-001 format)
- Never makes architectural decisions
- Never generates requirements or requirement contracts
- Never interacts with Spec Gate directly

**plan.md derivation rule**

- `plan.md` requirements come **EXCLUSIVELY** from `tasks.json`.
- `analysis.md` provides WHERE context only.
- If `tasks.json` and `analysis.md` conflict → `tasks.json` wins. Stop and report.

**Session management tasks (`ses-` prefix)**

- Claude Code may generate **INTERNAL SESSION TASKS** in `ses-YYYYMMDD-NNN` format.
- These are written to `~/.claude/tasks.json` **ONLY**.
- These are **NOT** PDOS project tasks.
- They do **NOT** enter the Spec Gate → Operator pipeline.

---

### 2. UPDATE: `~/.claude/CLAUDE.md` — Canonical Task File section

**Current (broken):**

```markdown
## Canonical Task File — Project Hygiene
One file. One source of truth.
~/.claude/tasks.json   ← ALL tasks, ALL projects
Never create or write to a project-local tasks.json.
```

**Replace with:**

```markdown
## Task File Separation — Two Files, Two Purposes

These two files must NEVER be confused:

### Claude Code Session Tasks (ses- prefix)
File: ~/.claude/tasks.json
Producer: Claude Code (session management only)
Schema: ses-YYYYMMDD-NNN format
Purpose: Claude Code's internal work tracking for this session
Rule: Claude Code ONLY writes here. Never to project-root tasks.json.

### PDOS Project Tasks (TASK- prefix)
File: [project-root]/.claude/tasks.json
Producer: Spec Gate GPT ONLY
Schema: TASK-001 format (tasks_schema.json)
Purpose: Execution queue → SQLite → Dashboard → Operator GPT → Claude Code
Rule: Claude Code READS this file to build plan.md. Claude Code NEVER WRITES to it.

Claude Code writing TASK-001 format entries = system violation.
Spec Gate writing ses-YYYYMMDD-NNN entries = system violation.
```

**Additionally** — update the “Step 2 / Decompose into tasks” section to add:

> NOTE: Tasks generated here are CLAUDE CODE SESSION TASKS (`ses-` prefix). They are NOT PDOS project tasks. They go to `~/.claude/tasks.json` ONLY. Never write these to `[project-root]/.claude/tasks.json`.

---

### 3. UPDATE: `~/.claude/CLAUDE.md` — Claude Code role clarification

Add a new section after “Core Principles”:

```markdown
## Claude Code Role in PDOS

Claude Code is the EXECUTION ENGINE, not an authority.

READS:
- tasks.json from project-root (Spec Gate output) → builds plan.md
- analysis.md from Gemini → codebase context for plan.md
- session.md → continuity

PRODUCES:
- plan.md (derived from tasks.json requirements + analysis.md context)
- Committed code
- Session task tracking (ses- format, ~/.claude/tasks.json only)

NEVER:
- Generates PDOS project requirements
- Writes to [project-root]/.claude/tasks.json
- Overrides Architect, Spec Gate, or Strategist decisions
- Treats Claude Code session tasks as PDOS authority
```

---

### 4. UPDATE: `MGPOD/Shared documents/core-agents-contracts/system_contract.md`

Add a section after “THE FOUR AGENTS”:

```markdown
## THE EXECUTION LAYER — CLAUDE CODE

Claude Code operates BELOW The Operator GPT in the pipeline.

Full pipeline (complete view):
User → Architect → Spec Gate → [tasks.json] → Operator GPT → Claude Code → Git

Claude Code:
- Reads tasks.json (Spec Gate output) to build plan.md
- Reads analysis.md (Gemini output) for codebase context
- Executes plan.md steps
- NEVER writes to tasks.json, project.md, or decisions.md
- NEVER generates PDOS requirements or requirement contracts

The Operator GPT manages sessions and invokes Claude Code.
Claude Code executes within the Operator GPT's constraints.
```

---

### 5. UPDATE: `MGPOD/Agent documentation/tier-1/master-document.md`

In Section 9 “Tool Strategy” under “Claude Code”, add:

```markdown
### Claude Code boundary in PDOS

Claude Code does not author requirements. Claude Code does not produce tasks.json.
Claude Code does not make architectural decisions.

Claude Code reads tasks.json (Spec Gate output) and analysis.md (Gemini output)
to produce plan.md. Requirements come ONLY from tasks.json.
```

---

## Flow diagrams (aligned — final state)

### Full pipeline with baton system

```
┌──────────────────────────────────────────────────────────────────────┐
│                    PDOS PIPELINE — ALIGNED                           │
└──────────────────────────────────────────────────────────────────────┘

AUTHORITY LAYER (ChatGPT):
  User
    │
    ├──► Aux Agents (7 specialists)
    │         │
    │         └──► proposal_[YYYYMMDD]_[agent-role].md ──► Architect GPT (validates)
    │                                       │
    ▼                                       │
  Architect GPT ◄─────────────────────────┘
    │
    ├── Produces: project.md (Section A: full PRD)
    │                        (Section B: machine baton)
    └── Produces: schema.json (project data model)
    │
    ▼
  Spec Gate GPT (consumes Section B ONLY)
    │
    └── Produces: [project-root]/.claude/tasks.json (TASK-001 format)
    │
    ▼
  Import Worker ──► SQLite ──► Dashboard ──► Human Approval
    │
    ▼
  Operator GPT (reads tasks.json + session.md)
    │
    ├── Delegates analysis to: Gemini CLI ──► analysis.md
    │
    ▼
  Claude Code (EXECUTION LAYER)
    │ Reads: tasks.json (WHAT), analysis.md (WHERE)
    │ Produces: plan.md
    │
    ├── Simple steps ──► Codex ──► handoff.md
    │
    └── Committed code ──► Git ──► session.md (Operator GPT writes)

ADVISORY LAYER (on-demand, not sequential):
  Strategist GPT ──► decisions.md (when execution hits architectural decision)

CLAUDE CODE SESSION LAYER (internal only):
  Claude Code ──► ~/.claude/tasks.json (ses-YYYYMMDD-NNN format)
  [NEVER enters PDOS pipeline. Internal tracking only.]
```

### Authority map

```
┌─────────────────────────────────────────────────┐
│  ARTIFACT         │  SOLE AUTHORITY              │
├───────────────────┼──────────────────────────────┤
│  project.md §A    │  Architect GPT               │
│  project.md §B    │  Architect GPT               │
│  schema.json      │  Architect GPT               │
│  tasks.json       │  Spec Gate GPT               │
│  session.md       │  Operator GPT                │
│  decisions.md     │  Strategist GPT              │
│  analysis.md      │  Gemini CLI                  │
│  plan.md          │  Claude Code (read-derive)   │
│  handoff.md       │  Codex                       │
│  proposal file    │  Aux Agents (non-authoritative)│
│  ~/.claude/tasks  │  Claude Code (session only)  │
└─────────────────────────────────────────────────┘
```

---

## Enforced ruleset (final)

| Rule | Statement |
|------|-----------|
| **R1** — tasks.json separation | `[project-root]/.claude/tasks.json` = Spec Gate output. Claude Code **READS**, **NEVER** writes. `~/.claude/tasks.json` = Claude Code session tracking. Claude Code writes here **ONLY**. |
| **R2** — Claude Code is not an authority | Claude Code produces `plan.md` and code only. Never requirements. Never `tasks.json` entries (PDOS). Never architectural decisions. |
| **R3** — plan.md derivation | `plan.md` **REQUIREMENTS** come **ONLY** from `tasks.json` (Spec Gate output). `analysis.md` provides **WHERE** context (Gemini). Not authority. If they conflict: `tasks.json` wins. Stop and flag. |
| **R4** — Aux agents are advisory | Aux agents produce date-stamped proposal files only. Non-authoritative. Routes through Architect before any system change. |
| **R5** — Architect is sole authority | No artifact enters the execution pipeline without Architect validation. Aux agents → proposal file → Architect → Section A/B → Spec Gate. No shortcuts. |
| **R6** — No agent bypasses the baton system | Every tool reads what the upstream tool produced. Gemini → `analysis.md` → Claude Code → `plan.md` → Codex → `handoff.md`. |
| **R7** — Session tasks are not PDOS tasks | `ses-YYYYMMDD-NNN` format entries are Claude Code internal session management. They **NEVER** enter the PDOS pipeline. They **NEVER** become TASK-001 entries without going through Architect → Spec Gate. |
| **R8** — The Operator is human-gated | No execution begins until `tasks.json` is imported, dashboard shows tasks, and human approves scope. |

---

## List of fixes (after approval)

| # | Fix | File | Type |
|---|-----|------|------|
| F1 | Create Claude Code contract document | `MGPOD/Shared documents/core-agents-contracts/claude_code_contract.md` | NEW FILE |
| F2 | Rewrite Canonical Task File section | `~/.claude/CLAUDE.md` | EDIT |
| F3 | Add Claude Code role clarification | `~/.claude/CLAUDE.md` | EDIT (new section) |
| F4 | Add Claude Code to execution layer | `MGPOD/Shared documents/core-agents-contracts/system_contract.md` | EDIT |
| F5 | Add Claude Code boundary in tool strategy | `MGPOD/Agent documentation/tier-1/master-document.md` | EDIT |
| F6 | Add `ses-` prefix note to Session Start Step 2 | `~/.claude/CLAUDE.md` | EDIT |

---

## Remaining risks after fixes

| ID | Risk |
|----|------|
| **RR1** | The canonical task file rule needs **enforcement**, not just documentation. Even after updating CLAUDE.md, Claude Code may still write to project-root `tasks.json` if given ambiguous instructions. A pre-tool hook or explicit schema ID check (`ses-` vs `TASK-`) would make this machine-enforced. |
| **RR2** | `plan.md` is ephemeral but may carry stale requirements. If `tasks.json` is regenerated by Spec Gate mid-session but Claude Code already has a `plan.md`, `plan.md` will be stale. No current mechanism alerts Claude Code to re-derive `plan.md` when `tasks.json` changes. |
| **RR3** | Multiple proposal files with no version tracking metadata beyond filename. Aux agents can produce multiple proposals. No current system tracks which proposal file was reviewed vs rejected vs promoted into Section A beyond the file contents. |
| **RR4** | Strategist’s `decisions.md` can contradict `tasks.json`. If the Strategist makes a decision that changes task scope **after** `tasks.json` was generated, the system has no mechanism to detect `tasks.json` drift. The Operator GPT is supposed to catch this, but it depends on the Operator reading both files and comparing. |

---

## Verification plan

After implementing fixes:

1. **Test R1:** Ask Claude Code (in a new session) to “add a task for building the auth module.” Verify it writes to `~/.claude/tasks.json` with `ses-` prefix, **NOT** to any project-root `tasks.json`.
2. **Test R2:** Ask Claude Code to “generate requirements for the dashboard tab.” Verify it refuses and redirects to Architect GPT.
3. **Test R3:** Feed Claude Code a `tasks.json` with a task and an `analysis.md`. Verify the resulting `plan.md` contains no requirements not present in `tasks.json`.
4. **Test R4:** Ask an aux agent (e.g. Senior Dev) to produce a `tasks.json` entry. Verify it refuses and produces a proposal file instead.
5. **Test R5:** Read all updated documents and verify no ambiguity remains about who owns what artifact.

---

## Critical files touched by this plan (when executed)

- `~/.claude/CLAUDE.md` — global Claude Code harness instructions
- `MGPOD/Shared documents/core-agents-contracts/system_contract.md` — shared pipeline contract
- `MGPOD/Shared documents/core-agents-contracts/claude_code_contract.md` — new Claude Code role definition
- `MGPOD/Agent documentation/tier-1/master-document.md` — tool strategy clarification
