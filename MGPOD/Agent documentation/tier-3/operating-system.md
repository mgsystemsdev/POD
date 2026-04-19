# Operating System

## System purpose

The Personal Developer Operating System is a structured, context-driven environment that turns ideas into **approved, traceable, executable** software work. It reduces context loss and enforces professional discipline for solo developers by separating:

| Concern | Role |
| :--- | :--- |
| **Authored knowledge** | Files (PRD, tasks, session, decisions) |
| **Operational state** | SQLite + dashboard |
| **Execution** | CLI/IDE tools |

The stack governs AI-assisted execution through a **tiered hierarchy** to cut re-explanation and improve token ROI.

---

## Inputs

| Input | Description |
| :--- | :--- |
| **Global memory** (`~/.claude/memory/`) | Operator identity (`user.md`), standards (`preferences.md`), durable decisions. |
| **Project context** (`.claude/context/`) | `project.md`, `tasks.json`, `session.md`, `decisions.md`. |
| **Codebase awareness** | Repo access via `CLAUDE.md`, `.cursor/rules/`. |
| **Step 0 analysis** | `analysis.md` from power tools or fallbacks to reduce implementation uncertainty. |

---

## Outputs

| Output | Description |
| :--- | :--- |
| **Operational state** | SQLite tables mirroring project truth for the dashboard. |
| **Surgical edits** | Minimal, atomic changes to files named in approved plans. |
| **Verification evidence** | Logs, tests, or screenshots proving the task **done condition**. |
| **Git lifecycle** | Task branches, atomic commits (1:1 with tasks), GitHub PRs for self-review. |

---

## Key entities and schema

| Entity | Definition |
| :--- | :--- |
| **Requirement contract** | Trigger, input, output, constraints, failure path — before implementation. |
| **Task object** | `id`, title (scope/sub-scope), description, `requirement_ref`, `success_criteria`, `failure_behavior`. |
| **Baton files** | `analysis.md`, `plan.md`, `handoff.md` — hand off context without full re-reads. |
| **Handoff summary (Section B)** | Compact PRD slice for execution tools. |

---

## Workflow — inner loop

| Phase | What happens |
| :--- | :--- |
| **Thinking (Layer 1)** | Architect GPT designs; Spec Gate GPT → atomic tasks in `tasks.json`. |
| **Sync (Layer 3)** | `agents push` mirrors disk → SQLite; regenerates thin tool pointers. |
| **Preparation** | Gemini CLI (fallback) can produce `analysis.md` at scale before Claude Code. |
| **Planning** | Claude Code in **Plan mode** → `plan.md` for approval. |
| **Execution** | **Codex** — steps from `plan.md`. **Cursor** — UI, single-file, tests. |
| **Automation** | **OpenCode** — only after a pattern is manually verified **three** times. |
| **Optimization** | **Kiro** — cleanup and performance after the feature is done. |
| **Verification & closeout** | Operator GPT checks contract, plain-English summary, Git PR/merge flow. |

---

## Constraints

- **WIP = 1** — one task in progress.
- **Git discipline** — no direct writes on `main`; isolated branch + GitHub PR per task.
- **Plain English** — operator-facing explanations in paragraphs, not code blocks in translation sections.
- **Automation gate** — never automate a step that has not been manually run and verified.

---

## Edge cases

| Case | Response |
| :--- | :--- |
| **Claude Code budget exhausted** | Pivot to Gemini CLI for reasoning, Cursor for focused execution. |
| **Design drift** | Stop; Architect / PRD update (Mode 2). |
| **Unclear tasks** | Reject tasks without a testable done condition; return to Spec Gate. |

---

## State handling

- **Persistence** — Git-tracked files are primary truth; SQLite is the operational mirror.
- **Continuity** — `session.md` at every session end; read at session start.
- **Registry** — `projects_index.json` maps slugs → absolute paths for workers/CLI.

---

## Failure handling

- **Fail loudly** — workers and sync succeed visibly or report failure; no silent failures.
- **Correction loop** — failed verification → diagnostic + fix prompt, not guessing.
- **RESET** — major structural failure → stop execution, document, return to Architect stage.

---

## Examples

### New feature setup

Raw idea → Architect (five-element contracts) → `project.md` Section B → Spec Gate → `tasks.json` → `agents push` → dashboard.

### Feature implementation

Select `TASK-012` → Step 0 / analysis → Plan mode → Codex surgical change (e.g. `auth.py`) → Operator verifies vs contract → PR opened.
