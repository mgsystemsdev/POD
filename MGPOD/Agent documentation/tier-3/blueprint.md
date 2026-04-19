# Blueprint

> **SYSTEM BLUEPRINT — PERSONAL DEVELOPER OS Version 1.4 — Complete, Internally Consistent, Execution-Safe**

---

## Section A — Project definition
#### 1. System overview
This system is a personal developer operating system designed to transform raw ideas into approved, traceable, and executable work through a structured, context-driven pipeline.

It enforces:

- Continuity across sessions  
- Requirement-backed execution  
- Human-governed state transitions  
- Single source of truth across tools  

The system separates:

- **Authored knowledge** (files)  
- **Operational state** (database)  
- **Execution** (tools)  

…to eliminate context drift, AI guessing, and workflow fragmentation.

---

#### 2. Core problem

Current workflows fail due to:

- Context loss between sessions  
- AI generating incorrect outputs due to missing constraints  
- Non-executable task outputs  
- Fragmented state across tools  
- PRD drift and decision loss  
- Lack of enforced execution discipline  

---

#### 3. Users
Primary User: Solo developer (Miguel Gonzalez)
Agents: Internal system components, not users
Future: Multi-user support (out of scope for V1)

---

#### 4. Success criteria (V1)

The system is successful if:

- Session startup takes under 2 minutes with full context restored  
- Three full cycles complete with zero manual patching  
- All tasks have testable success criteria  
- Git shows 1:1 mapping between tasks and commits  
- Code matches PRD with zero drift  
- Strategic decisions are retrievable and reusable  

---

#### 5. Requirements

---

### REQ-001 — PRD Generation (Architect)
**Trigger:** User provides idea to Architect
**Input:** Natural language with defined goal
**Output:**
project.md (Section A + Section B)
schema.json
Handoff instructions
**Constraints:**
Full 5-element requirement contracts
No assumptions
No conflicts
MVP defined
Includes full backend + UI
Single-session completion
No partial output
**Failure Path:**
Block output
Ask one critical question
Trigger 3-option protocol if needed

---

### REQ-002 — Task Generation (Execution Spec Gate)
**Trigger:** User provides Section B
**Input:** Valid structured baton from Architect
**Output:**
tasks.json (single valid JSON array)
**Constraints:**
Atomic tasks only
No conversational pauses
Infrastructure first
Valid JSON only
Tasks decomposed into scopes of 5-15 tasks
Large scopes must be split into sub-scopes
No arbitrary hard caps — scope drives decomposition
**Failure Path:**
No output
Ask for clarification
Block on conflict

---

### REQ-003 — Task Ingestion (Control Plane)
**Trigger:** User runs CLI (agents push / agents tasks)
**Input:** Valid tasks.json
**Output:**
Tasks stored in DB
Dashboard updated
**Constraints:**
Atomic ingestion (all-or-nothing)
No partial writes
**Failure Path:**
Entire ingestion fails
No DB changes
User must fix input

---

### REQ-004 — Task Execution (Operator)
**Trigger:** User selects task and provides to Operator
**Input:** Task + PRD + session context + analysis.md
**Output:**
Git branch created
Execution prompt delivered
Task moves to in_progress
plan.md produced before any code is written
**Constraints:**
WIP = 1
Git branch required
No blind execution
Claude Code must enter plan mode before executing
Plan must be approved before any file is written
**Staleness Detection:** Every `plan.md` must carry a `TASKS_CHECKSUM` header. If the checksum of the current `tasks.json` differs from the plan header, the plan is stale and must be re-derived.
Step 0 analysis required before planning begins
Minimal changes only — only files listed in plan
No assumptions — unclear means stop and ask
**Failure Path:**
Block if task unclear
Block if context missing
Block if Git dirty
Block if plan not approved
Block if analysis.md missing for complex tasks

---

### REQ-005 — Session Continuity
**Trigger:** Operator session start
**Input:** session.md + project context
**Output:**
Restored session state
Next task identified
**Constraints:**
Mandatory before execution
No guessing
**Failure Path:**
Block execution until resolved

---

### REQ-006 — Project Onboarding (agents init)
**Trigger:** User runs agents init on a new project path
**Input:** Project path + slug + name
**Output:**
.claude/context/ bundle created
CLAUDE.md generated (two-section structure)
.cursor/rules/ generated (same source, different format)
.claude/docs/ generated (one spec file per dashboard tab)
projects_index.json updated (both copies)
SQLite project row created
agents push runs automatically
Validation report printed
**Constraints:**
Idempotent — safe to run twice
Fails loudly at each step with rollback instructions
Never overwrites existing context files
Global .cursor/rules/ created once if missing
Each sub-step is independently retryable
**Failure Path:**
Each sub-step fails independently with clear message
Nothing is registered until all steps succeed
User told exactly which step failed and how to retry
Partial state is reported — not silently ignored

---

### REQ-007 — Tool Configuration Sync
**Trigger:** agents init or agents push
**Input:**
~/.claude/memory/ files (global source)
.claude/context/ files (project source)
**Output:**
project/CLAUDE.md regenerated (system section only)
project/.cursor/rules/00-context.mdc regenerated
Both tools point to same .claude/context/ folder
**Constraints:**
One direction only — memory files to tool configs
Tool configs are pointers, not content copies
/init codebase section of CLAUDE.md never overwritten
~/.cursor/rules/ global config created once
If generation fails — ingestion does not proceed
System blocks and reports which file failed
**Failure Path:**
Log which file failed to generate
Block agents push from completing
Report all missing outputs before exiting
User must fix and re-run

---

### REQ-008 — Task Verification
**Trigger:** Execution tool completes output — Operator requests evidence
**Input:**
Required (all tasks):
1. **Success Criteria:** Traceable to REQ-### in PRD.
2. **Git Diff:** `git diff` output showing ONLY the files listed in `plan.md`.
3. **Objective Evidence:** Raw terminal output, test results, or linter logs.
Context-specific evidence:
Backend tasks: test results, command output, migration logs.
UI tasks: screenshots compared against design or PRD requirements.
Infrastructure tasks: API response validation, permission audits.
Valid input conditions:
Objective and observable
Directly addresses done condition
No unexpected changes in diff
Covers constraints and failure paths defined in contract
Invalid input:
Subjective claims ("it works", "looks right")
Missing evidence or missing diff
Partial validation (happy path only)
Violates architectural constraints from decisions.md
**Output:**
PASS:
Task status remains in_progress (not done yet)
Branch cleared for Commit Gate
System enters Review-Ready state
Artifacts produced:
Plain English explanation of what was built
Self-review checklist
Exact commit command
FAIL:
Task status remains in_progress
Run recorded as failure in history
No commit permitted
Branch remains active and dirty
System enters Correction Loop
Artifacts produced:
Diagnostic explanation of why contract was not met
Fix prompt (copy-ready for execution tool)
**Constraints:**
Claude Code self-verifies before reporting completion
Self-verification output becomes the primary evidence
Human provides supplementary evidence only when Claude Code cannot self-verify (UI screenshots etc.)
No task can move to done without passing verification
Verification must match success criteria
Evidence is required — descriptions rejected
Operator must fail loudly — no silent acceptance
**Failure Path:**
Reject invalid or incomplete evidence
Block commit and pipeline progression
Return to execution with fix prompt
Log failure in Run history

---

### REQ-009 — Task Completion
**Trigger:** User manually marks task as Done in dashboard.
**Full sequence:**
1. PR merged to `main` via GitHub.
2. Local branch deleted.
3. `git pull` run to update local `main`.
4. User confirms local `main` is clean and updated.
5. User clicks **Complete** in dashboard.
6. API call — `POST /api/tasks/{id}/complete`.
7. DB updated — task to `done`, run to `success`.
**Input:**
Task in `in_progress` state
Verified implementation (REQ-008 passed)
Clean local `main` reflecting merged code
**Output:**
Task status moves to `done`
Run marked as `success`
Dashboard reflects completed state
System enters stable baseline
User runs `agents push` — session state mirrored to DB
**Constraints:**
Cannot mark done unless PR is merged
Cannot mark done unless local `main` is updated
Must be manual — human-gated
Must follow verification (REQ-008)
`agents push` required after completion to lock state
**Failure Path:**
If PR not merged — block completion
If local not synced — block completion
If task not verified — block completion
If user attempts bypass — reject API call

---

### REQ-010 — ProposedAction Lifecycle
**Trigger:** Any internal system agent attempts to modify project state.

**Trigger sources:**

- Internal agent write requests (planner, create, merge — tasks, files, structures)  
- Autonomous task decomposition  
- File/code modification attempts (diffs, new files)  
- Scope drift detection vs PRD  
- System maintenance (decision reviews, health audits)  

**Critical constraint:**
Only internal agents generate ProposedActions in V1
User input goes through Architect and Spec Gate — not ProposedAction
ProposedAction is the internal autonomy safety valve
**Input:**
Agent-generated proposal (task, diff, decision, etc.)
Metadata: action_type, source_agent, impact_level, reversibility, payload
**Output:**
User visibility (Dashboard — Actions Tab):
Pending queue showing:
Action type
Plain English description
Source agent
Impact level (High / Medium / Low)
Reversibility indicator
Timestamp
Recently decided history showing approved and rejected entries
User actions:
Approve
Reject (with optional feedback note)
View Details (inspect raw payload or diff)
**On Approval:**
POST /api/proposed-actions/{id}/approve
ProposedAction committed to system state
Task created, blueprint updated, or decision logged
Status moves to approved
Record moves to history
**On Rejection:**
POST /api/proposed-actions/{id}/reject
No state mutation occurs
Feedback optionally stored
Status moves to rejected
Record moves to history
**Full lifecycle:**
Agent calls proposed_action_service — record written as pending
Dashboard reflects new entry in Actions tab
User reviews proposal against requirement contracts
User approves or rejects
System commits or discards
Record archived with terminal status
**Constraints:**
No internal agent can mutate system state without passing through ProposedAction
This includes tasks, blueprints, and decisions
No direct writes to primary tables from any agent
All writes are auditable and human-authorized
**Failure Path:**
Agent attempts direct write — rejected by service layer
ProposedAction rejected by user — no state change
Proposal loops blocked — rejection feedback halts agent reasoning

---

#### 6. Data model

**Entities:** Project, Task, Run, ProjectBlueprint, Decision, SessionLog, ProposedAction.

**Relationships (summary):**

- Project → tasks, decisions, sessions, proposed actions  
- Task → runs  
- ProposedAction → tasks (1:N)  
- Project → project blueprint (versioned)  
- Task → blueprint via `requirement_ref`  

**Task (core facets):** identity (`task_id`, `project_id`); definition (title, description, status); hierarchy (scope, tier, dependencies); execution contract (`success_criteria`, `failure_behavior`); metadata (timestamps, notes, `correlation_id`).

**SQLite tables:** `projects`, `tasks`, `runs`, `blueprints`, `decisions`, `session_logs`, `proposed_actions`, `schema_version`.

**Memory:** not a primary DB table — file-first in `.claude/context/`; optional dashboard mirror; **file wins**.

**Dashboard:** Blueprint and Decisions **read-only** in UI; edit on disk only.

---

#### 7. System workflow

1. Idea → Architect → `project.md`  
2. `project.md` → Spec Gate → `tasks.json`  
3. CLI push → atomic DB ingestion  
4. Dashboard → review + approve  
5. Operator → session restore  
6. Select task → Git branch  
7. Gemini CLI → `analysis.md`  
8. Claude Code → plan mode → approved `plan.md`  
9. Execute (Claude / Cursor / Codex)  
10. Operator collects verification evidence; Claude self-verifies first  
11. PASS/FAIL → on PASS, commit gate  
12. Commit → PR → merge → pull local `main`  
13. Mark task done in dashboard  
14. `agents push` → lock state  
15. `session.md` + optional Kiro polish  
16. Repeat  

---

#### 8. System architecture

##### Layer 1 — Global memory

| | |
| :--- | :--- |
| **Owns** | Identity, preferences, standards |
| **Lives in** | `~/.claude/memory/` |
| **Never owns** | Project or operational state |
| **Files** | `user.md`, `preferences.md`, `decisions.md`, `agent_stack.md` |

##### Layer 2 — Project context

| | |
| :--- | :--- |
| **Owns** | Project truth |
| **Lives in** | `project/.claude/context/` |
| **Never owns** | Database or execution logic |
| **Files** | `project.md`, `tasks.json`, `session.md`, `decisions.md`, copies of user prefs, `MEMORY.md`, baton files |

##### Layer 3 — Control plane

| | |
| :--- | :--- |
| **Owns** | Operational state and visibility |
| **Lives in** | SQLite + dashboard at `localhost:8765` |
| **Never owns** | Authored truth |
| **Components** | FastAPI, SQLite, 10-tab dashboard, `proposed_actions` gate, workers |

##### Layer 4 — Execution interfaces

| | |
| :--- | :--- |
| **Own** | Execution and reasoning |
| **Never own** | Truth or state |
| **Components** | Claude Code, Gemini CLI, Cursor, Codex, OpenCode, Kiro |

---

## Section B — Component inventory

*The tool hierarchy — every component, one role.*

### Primary power tool — Claude Code

- Weekly token limit — used surgically, full week  
- Full planning and complex builds; multi-file reasoning; hard debugging  
- Plan mode before every task; self-verify before “done”  
- Open with context loaded (no cold opens); close after each task  

### Primary fallback — Gemini CLI

- Free budget, separate from Claude Code  
- Planning/reasoning when Claude Code is exhausted; feeds context before Claude opens  
- Large context window; produces `analysis.md`; reads `handoff.md` on fallback  

### Execution layer

**Codex**

- Separate budget; one step at a time from `plan.md`  
- Minimal changes, listed files only; produces `handoff.md`  

**Cursor**

- Separate budget; UI/frontend; single-file edits and tests  
- Reads `.cursor/rules/` automatically  

### Automation layer — OpenCode

- Separate budget; proven workflows only (after manual proof)  
- Replaces Codex loops for validated patterns  

### Optimization layer — Kiro

- Separate budget; cleanup/polish after features complete  
- Not for core logic; runs after Claude Code build phase  

### Thinking layer (ChatGPT)

| Agent | Budget | Role |
| :--- | :--- | :--- |
| Architect GPT | ChatGPT | Designs features → `project.md` |
| Spec Gate GPT | ChatGPT | Breaks work into tasks → `tasks.json` |
| Pipeline Strategist GPT | ChatGPT | Decisions → `decisions.md` |
| Operator GPT | ChatGPT | Sessions → `session.md` |

**Specialist agents** (7 auxiliaries) produce date-stamped proposal files with 8 required sections: Scope, Decisions, Options (A/B/C), Constraints, Risks, Invariants, System Impact, Open Questions.

### Sync layer — `agents push`

- Syncs disk → SQLite after sessions  
- Regenerates `CLAUDE.md` and `.cursor/rules/`  
- Updates dashboard; runs after task completion and session close  

---

### The baton files — token sharing between tools

Three files hand off context **without** re-reading the whole repo.

| File | Written by | Read by | Contains |
| :--- | :--- | :--- | :--- |
| `.claude/context/analysis.md` | Gemini CLI (before Claude opens) | Claude Code | Map of what exists, connections, what to change / not change, risks |
| `.claude/context/plan.md` | Claude Code (after plan approval) | Codex; Cursor | Ordered steps, files per step, per-step validation |
| `.claude/context/handoff.md` | Codex/Cursor per step; Claude before close | Operator GPT; Gemini on fallback | What changed, verification, what’s next |

No tool re-reads what another already processed; the baton moves forward and context accumulates without duplication.

---

### Component count (updated)

| Count | Component |
| :---: | :--- |
| 1 | Primary power tool (Claude Code) |
| 1 | Primary fallback (Gemini CLI) |
| 2 | Execution tools (Codex, Cursor) |
| 1 | Automation (OpenCode) |
| 1 | Optimization (Kiro) |
| 4 | ChatGPT agents (thinking layer) |
| 1 | Sync layer (`agents push` / `agentctl.sh`) |
| 1 | Dashboard + FastAPI |
| 1 | Database (SQLite) |
| 3 | Workers (task, sync, decision reviewer) |
| 1 | API key (Anthropic) |
| 2 | Config formats (`CLAUDE.md`, `.mdc`) |
| 1 | Knowledge bundle (`.claude/context/`) |
| 3 | Baton files |
| 1 | Registry (`projects_index.json`) |
| 2 | Version control (Git, GitHub) |

**Total:** 26 components across 7 layers.

---

## Section C — Tool configuration

### The middle point — one source, two doors

Claude Code and Cursor read the **same** project context. Neither duplicates stacks; both point at `.claude/context/`.

| Entry | Points to |
| :--- | :--- |
| `CLAUDE.md` | Claude Code |
| `.cursor/rules/00-context.mdc` | Cursor |

**`CLAUDE.md` structure**

- **Top half** — from `agents init` (memory files).  
- **Bottom half** — from `/init` (codebase scan).  
- Halves coexist; neither overwrites the other.  
- Keep **under 1500 tokens**; run `agents trim-claude` if bloated.  

`agents init` creates both adapters; `agents push` regenerates them. **Content lives in `.claude/context/`** — not duplicated in adapters.

---

### `CLAUDE.md` — token role declaration

Every `CLAUDE.md` should include a block like:

```markdown
## My role in this system

I am the primary power tool. I run at full power.
Before you opened me:
- Gemini CLI analyzed the codebase → read analysis.md
- GPT agents handled design conversation → read plan context
- Codex or Cursor attempted simple steps → read handoff.md

Read those three files first.
Never re-read the full codebase if analysis.md exists and is current.
Enter plan mode before every task.
Self-verify before reporting any task complete.
Write handoff.md before closing.
```

---

### `.cursor/rules/` — token role declaration

Every `.cursor/rules/00-context.mdc` should include a block like:

```markdown
## My role in this system

I handle UI, frontend, and single file work.
Claude Code handles multi-file complexity.

Before executing any step:
Read .claude/context/analysis.md if it exists.
Read your step from .claude/context/plan.md only.
Do not read the full plan — one step at a time.

After completing your step:
Write .claude/context/handoff.md.
Include: what changed, files touched, verification output.

If stuck: write what blocked you to handoff.md.
Stop. Claude Code will take over from handoff.md.
```

---

### `.claude/docs/` — dashboard tab documentation

Generated by `agents init`. One spec file per tab:

- `00-overview.md` … `10-health.md`  

Each file should define: **Trigger**, **Input**, **Output**, **Constraints**, **Failure path**, **API routes**, **Empty state**, **Error state**.

---

## Section D — Dashboard design

### Ten tabs in three groups

**Work (every session)**

| # | Tab | Role |
| :---: | :--- | :--- |
| 1 | Tasks | Queue, priority, mark complete |
| 2 | Actions | Proposed-actions approval gate |
| 3 | Session log | Continuity — what happened, what’s next |

**Knowledge (project memory)**

| # | Tab | Role |
| :---: | :--- | :--- |
| 4 | Blueprint | `project.md` rendered, read-only |
| 5 | Decisions | Architectural choices, append-only |
| 6 | Memory | Context files mirrored from disk, read-only |
| 7 | Preferences | Theme, autonomy placeholder |

**System**

| # | Tab | Role |
| :---: | :--- | :--- |
| 8 | Runs | Execution history |
| 9 | CLI | Log viewer, source, level filter |
| 10 | Health | DB alive, workers, status |

### Persistent UI

- **Sidebar** — project switcher, status dots  
- **Header** — project selector, pending task/action counts, Push, Refresh  
- **Alert strip** — only when attention needed; dismissible  

### Read-only rule

Blueprint, Decisions, and Memory are **read-only** in the UI. Author on disk; the dashboard is for **visibility and control**, not primary authoring.

### Human gate

The **Actions** tab is the most important surface: agents **propose**, you **approve or reject**. Nothing in `proposed_actions` becomes real without approval — at every version.

---

## Section E — The three versions

| | **V1** (local manual) | **V2** (ngrok + API) | **V3** (VPS 24/7) |
| :--- | :--- | :--- | :--- |
| **Agents write DB** | No — you copy | Yes — via API | Yes — HTTPS |
| **Workers run** | No / broken | Yes — scheduled | Yes — always on |
| **Laptop required** | Yes | Yes | No |
| **Available 24/7** | No | No | Yes |
| **API security** | None needed | API key | API key + HTTPS |
| **Cost** | $0 | $0 | ~$5/month |
| **You are** | The bridge | The approver | The decision maker |
| **Proven** | Not yet | After V1 | After V2 |

### V3 deployment: VPS over AWS

- SQLite wants a single machine — VPS fits.  
- ~$5/mo vs higher AWS floor; similar ops shape (systemd, Nginx, Certbot).  
- EC2 is an acceptable but costlier alternative; **serverless breaks** this SQLite architecture.  

**Non-negotiable:** prove V1 before V2; prove V2 before V3 — no skipping.

---

## Section F — Current state

| Track | Status |
| :--- | :--- |
| **V1** | ~40% — foundation built, full cycle not completed |
| **V2** | 0% — waiting on V1 |
| **V3** | 0% — waiting on V2 |

### What is built

- Dashboard at `localhost:8765`  
- SQLite with data (example: 152 tasks, 4 projects)  
- Workers: task, sync, decision reviewer  
- CLI: push, init, dashboard, tasks  
- Four GPT agents defined and tested  
- REQ-001 … REQ-010 specified  

### What is broken

- `task_worker` — `ANTHROPIC_API_KEY` not set  
- `decision_reviewer` — uses bare `python3` vs required `python3.13`  
- `db.py` — hardcoded path, not portable  
- `.claude/context/` — missing on registered projects (example snapshot)  

### What is missing

- One complete end-to-end cycle  
- `agents init` as orchestrated sub-commands  
- `CLAUDE.md` + `.cursor/rules/` from one source  
- `.claude/docs/` generated on init  
- Health monitor across components (V2)  
- Baton templates on init  
- `agents trim-claude`  

### Next actions

Execute home directory migration; fix the three broken items; redesign `agents init`; build dashboard Session 1; run first full cycle on a **small** project.

---

## Section G — System invariants

These rules never change at any version.

1. Files are the source of truth. DB is the mirror.  
2. No task is done until merged, pulled, and human-confirmed.  
3. No agent writes directly to tasks, blueprints, or decisions.  
4. All agent writes pass through `ProposedAction`.  
5. Blueprint and Decisions are read-only in the dashboard.  
6. WIP limit is 1 — one task in progress at all times.  
7. Every task has a testable done condition before execution starts.  
8. Verification must pass before commit gate opens.  
9. `session.md` is written at the end of every session without exception.  
10. V1 proven before V2; V2 before V3 — no skipping.  
11. Never optimize prompts — optimize context (model improves monthly; invest in `.claude/context/`).  
12. Long one-off prompts belong in `CLAUDE.md` or `.claude/context/` as permanent context.  
13. Analyze before planning; plan before executing. Unclear analysis → stop and fix understanding.  
14. Per step: minimal changes, only listed files, no assumptions, one step at a time — never batch steps.  
15. Never automate until manually executed and verified; automation is earned.  
16. `CLAUDE.md` under 1500 tokens — prune or regenerate from memory if bloated.  
17. Claude Code at full power on hard problems — eliminate waste so the weekly budget lasts.  
18. Every Claude Code session opens with context loaded (`analysis.md`, `plan.md`, `session.md`) — zero cold opens.  
19. Claude Code plans and builds; Codex executes simple steps; Cursor does files/UI; OpenCode automates proven work; Kiro cleans up; Claude closes after each task.  
20. Gemini CLI is the fallback — feed baton files; work continues when Claude budget is exhausted.  
21. Baton handoff (`analysis.md` → `plan.md` → `handoff.md`) — no redundant full re-reads.  
22. OpenCode only after manual proof — same automation rule as (15).  
23. `plan.md` must match `tasks.json` checksum. No execution from stale plans.

---

## Section H — Token budget and surgical use

### Core principle

Claude Code runs at **full power** with **zero waste**. Other tools feed context and catch output so the **weekly** limit can last seven days.

### Where the budget burns in three days

| Wasteful pattern | Fix |
| :--- | :--- |
| Cold open — full codebase read | Gemini CLI writes `analysis.md` first |
| Long design in Claude | GPT agents design before opening Claude |
| Babysitting Codex | Claude plans; Codex executes alone |
| Cleanup/optimization in Claude | Kiro |
| Repeating proven workflows | OpenCode after first manual proof |
| Session left open between tasks | Close after each task; reopen fresh |

### Surgical Claude Code session

| Phase | Tokens | Focus |
| :--- | :--- | :--- |
| **Open** | Minimal | Read `analysis.md`, plan context, `session.md`; skip full re-read |
| **Plan** | Full | Architecture, multi-file reasoning, hard problems → approved `plan.md` |
| **Build** | Full | Multi-file implementation, integrations, debugging |
| **Close** | Minimal | `handoff.md` (<300 words), `agents push`, close — Codex/Cursor/Kiro continue |

### Daily budget (~14% per day)

| Day | Focus |
| :--- | :--- |
| **Monday** | Gemini + GPT: analysis/design; Claude heavy planning (~14%); Codex simple steps |
| **Tuesday** | Operator session; Claude complex build (~14%); Codex; Cursor UI |
| **Wednesday** | Claude architecture/hard problems (~14%); Codex; OpenCode for proven loops |
| **Thursday** | Claude debug/review (~14%); Kiro; Cursor edits |
| **Friday** | Claude verify/close (~14%); Kiro; Operator week `session.md`; `agents push` |
| **Weekend** | Buffer or roll forward |

### Session opening protocol

1. **Context, not raw repo** — read `analysis.md` and `plan.md` first; map is in `analysis.md`.  
2. **State the goal** — today’s outcome, files from analysis, plan location.  
3. **Plan mode** — Shift+Tab ×2; approve plan before code.  
4. **Close** — short `handoff.md`, `agents push`, exit Claude.  

### Daily routing check (before opening Claude)

1. Can Gemini analyze this?  
2. Can a GPT agent design this?  
3. Can Codex run this step?  
4. Can Cursor touch this file?  
5. Can Kiro or OpenCode do this?  

Open Claude only if all five are **no**, or the task needs real **multi-file** complexity.

### Budget red flags

| Red flag | Meaning |
| :--- | :--- |
| Claude reads repo cold | Route to Gemini first |
| Claude on single-file edits | Route to Codex/Cursor |
| Claude doing design chat | Route to GPT agents |
| <50% budget left before Wednesday | Routing breakdown |
| Codex/Kiro/OpenCode unused | Under-using the stack |
| No `analysis.md` | Skipping analysis |
| Budget gone by Thursday | Full discipline failure |

### Fallback protocol (Claude exhausted)

**Primary fallback:** Gemini CLI.

1. **Keep working** — switch to Gemini immediately.  
2. **Feed baton files** — prompt Gemini with `analysis.md`, `session.md`, `plan.md`, `handoff.md` and continuation instructions.  
3. **Full stack** — Gemini (planning) → Codex → Cursor → OpenCode → Kiro.  
4. **Log** — append to `decisions.md` (date, switch, anti-pattern).  
5. **Monday post-mortem** — adjust routing.  

Example Gemini wrapper (adjust paths as needed):

```text
gemini "Read: .claude/context/analysis.md, session.md, plan.md, handoff.md
You are taking over from Claude Code. Continue from where it stopped."
```

---

### Boris principles (integrated)

#### Plan mode

- ~80% of sessions start in plan mode (Shift+Tab ×2).  
- Plan approved before first file write — reflected in REQ-004.  

#### Minimal `CLAUDE.md`

- Stay under 1500 tokens; `agents trim-claude` when bloated; regenerate from memory if severe.  
- Add rules only when the model errs — not preemptively.  

#### Self-verification

- Claude checks its work before “done”; human adds evidence when needed (e.g. UI) — REQ-008.  

#### Parallel sessions

- V2, after three proven cycles; max two non-overlapping sessions; fresh session if stuck >20 min; **WIP = 1** for V1.  

#### Inner loop skills

- Discover **after** the first cycle; build skills for patterns repeated >2×, e.g. `/session-start`, `/session-end`, `/task-start` (incl. Step 0), `/task-done`.  

#### Build for the future

- Invest in **context** (`.claude/context/`), not one-off prompt tuning.  

---

## Section I — Missing and future

### Known gaps (V1)

| Item | Notes |
| :--- | :--- |
| **Health monitor** | Proactive component watch (Health tab is partial); **V2**. |
| **Parallel session management** | Two Claude sessions, non-overlapping files — **V2** after three cycles. |
| **`agents trim-claude`** | Prune `CLAUDE.md` over token limit — small CLI add. |
| **Baton templates** | Empty `analysis.md` / `plan.md` / `handoff.md` on `agents init` — not yet scaffolded. |

### V2 additions

- Health monitor; parallel-session rules.  
- ngrok; agents write DB via API.  
- API key middleware; CORS for ChatGPT actions.  
- `GET /api/projects/by-slug/{slug}`; `POST /api/tasks/batch`.  
- Inner-loop skills from first three cycles.  

### V3 additions

- VPS (e.g. Hetzner, DigitalOcean); systemd; Nginx `:443`; Let’s Encrypt.  
- Daily SQLite backup to cloud; stable domain; phone-friendly access.  
- Portable `db.py` (`Path.home()`); regenerate `projects_index.json` on deploy.  
