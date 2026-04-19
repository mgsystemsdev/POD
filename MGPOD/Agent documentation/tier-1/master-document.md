# Master document

The canonical map for this documentation set is the [Documentation index](../README.md).

## Master strategy document

**Personal Developer Operating System**  
*Context-Driven Execution System for Solo AI-Assisted Software Delivery*  
Version 1.4 — Complete, Execution-Safe, Tool-Routed

---

## 1. Executive summary

This system is a personal developer operating system: a structured environment that turns ideas into approved, traceable, executable work. It sits between ideation, planning, execution, and system memory so that each stage produces reliable inputs for the next. Its purpose is not to replace judgment. Its purpose is to reduce re-explanation, eliminate hidden state, enforce disciplined execution, and create continuity across tools, sessions, and projects.

**Pipeline (five GPT agents):** Blueprint Creator (GPT-0) → Architect (GPT-1) → Execution Spec Gate (GPT-2) → [Pipeline Strategist (GPT-3, on-call)] → Operator (GPT-4) → Claude Code → Git.

Blueprint Creator is the entry point for any user with any idea. It produces a nine-document draft bundle that the Architect validates into `project.md`. This makes the system accessible to non-technical users without changing the Architect's authority over canonical artifacts.

> **Two Strategists:** The **Pipeline Strategist** (GPT-3, on-call during execution) is distinct from the **Auxiliary Strategist** (`Official agents/core/strategist/`). Pipeline Strategist owns `decisions.md` — canonical. Auxiliary Strategist produces advisory date-stamped proposal files only. See `Agent documentation/tier-1/gpt-layer-index.md` for the full disambiguation.

The system has three strategic goals:

1. **Stable knowledge substrate** — work does not restart from scratch each session.
2. **Operational control plane** — project state is visible, reviewable, and auditable.
3. **Tool-independent context layer** — Claude Code, Cursor, Gemini CLI, and future interfaces share one source of truth instead of diverging copies.

This is what makes the system more than a dashboard or a prompt collection. It is an execution environment with memory, control, boundaries, and deliberate tool routing across a budget-conscious multi-tool stack.

The long-term vision is an always-on service that can accept structured work from external agents, hold it safely behind approval boundaries, and support disciplined execution from any terminal. The near-term priority is not scale. It is reliability. The system only earns the right to move to remote access and VPS deployment once one full local cycle works cleanly, repeatedly, and without manual patching between steps.

---

## 2. Problem statement

Most development workflows break in the same places. Requirements are vague. Tasks are not executable. Decisions are lost in chat history. Context disappears between sessions. AI tools receive partial information and fill gaps by guessing. State exists in too many places at once: notes, chats, files, dashboards, memory, and git history. The result is friction, drift, and false confidence.

Traditional task systems do not solve this. They track work items, but they do not preserve requirement contracts, decision history, session continuity, or execution constraints in a form that an AI tool can use directly. Prompting alone does not solve it either, because prompting without persistent system context just recreates the same explanation burden every session.

A further problem unique to AI-assisted development is **token budget exhaustion**. When a single tool handles analysis, planning, execution, verification, and cleanup, its weekly token budget is consumed in days. The system must route work deliberately across a multi-tool stack so the primary power tool is reserved for work only it can do.

This operating system exists to solve five concrete problems:

- Context loss between sessions
- Execution without enough architectural context
- Uncontrolled writes from agents or automation
- Tool drift where each interface knows a different version of reality
- Token budget exhaustion from misrouted work

---

## 3. Strategic design principles

### 3.1 One source of truth per type of state

Project context belongs in the project. Global identity and preferences belong in a global memory layer. Approved operational state belongs in the database. Tools do not own knowledge. They read it.

### 3.2 Human approval at state boundaries

Nothing becomes operational reality until it passes through a human-reviewed boundary. This is not a temporary safety measure. It is a permanent architectural choice for any state that affects execution order, task queue integrity, or project truth.

### 3.3 Design by requirement, not by convenience

Each major component should be defined by trigger, inputs, outputs, constraints, and failure path. If a component cannot be described that way, it is not yet well designed.

### 3.4 Files for authorship, database for operational state

Files are the authoring medium and continuity medium. The database is the operational mirror and control plane. It should not become an undocumented second authoring system.

### 3.5 Thin tool adapters, not duplicated systems

Claude Code, Cursor, Gemini CLI, and future tools should receive thin entry files that point to shared context, not separate content stacks that require regeneration and drift correction.

### 3.6 Analyze before planning. Plan before executing.

No tool touches code without first understanding the system. No execution begins without an approved plan. Unclear analysis means stop — not proceed with assumptions.

### 3.7 Route work to the cheapest capable tool

Claude Code is the primary power tool. Every other tool in the stack exists to feed it context, catch its output, or handle work it does not need to touch. Misrouting work through Claude Code when another tool can handle it wastes the weekly budget on tasks that do not require its power.

### 3.8 Optimize context, not prompts

The model improves every month. Prompt optimization is a depreciating investment. Context quality — what lives in `.claude/context/` — is a permanent investment. Every long prompt is a signal of missing context that should be moved into the knowledge bundle permanently.

---

## 4. Target operating model

The system should be understood as four connected layers.

### Layer 1: Global memory layer

Contains stable information about the operator: identity, working preferences, standards, and durable global decisions. Lives in a global path, separate from any single repo. Its job is to brief any tool on who it is working with and how that person operates.

### Layer 2: Project context layer

Contains project-specific truth: what the project is, what was decided, what happened last session, and what work is pending. This is the live project knowledge bundle. It belongs inside each project so the project remains portable and self-describing.

It includes the three **baton files** that enable tool handoff without re-reading source:

| File | Writer | Readers |
| :--- | :--- | :--- |
| `analysis.md` | Gemini CLI | Claude Code |
| `plan.md` | Claude Code | Codex and Cursor |
| `handoff.md` | Codex or Cursor | Operator GPT; Gemini CLI (fallback) |

### Layer 3: Control plane

The database, API, dashboard, and approval workflow. Reflects approved operational state and provides visibility into what the system believes is true right now.

### Layer 4: Execution interfaces

Includes Claude Code, Gemini CLI, Cursor, Codex, OpenCode, Kiro, and any external or internal agent entry points. Their job is not to store truth. Their job is to read truth, execute within constraints, and propose changes through approved paths.

Each tool in Layer 4 has a defined role and a defined budget. No tool does another tool's job.

---

## 5. Source of truth model

The system must distinguish among three types of truth:

- **Global truth:** who the operator is, how they work, and global standards.
- **Project truth:** what this project is, why it exists, what changed, and what is next.
- **Operational truth:** what has been imported, approved, queued, run, or completed.

Project files are the source of **authored** context. The database is the source of **approved operational** state. Tool config files are not sources of truth at all — they are routing files.

A clean model:

- Global memory in a shared global folder
- Project context in project-local context files
- Database as approved mirror
- Tool config as thin pointers

Any design that requires regenerating large tool-specific context files on every push should be treated as a warning sign unless there is a proven need.

---

## 6. Knowledge schema

At minimum, each project needs a stable context schema.

| File | Role |
| :--- | :--- |
| `project.md` | What is being built and under what constraints |
| `tasks.json` | What gets executed next and how success is judged |
| `session.md` | Where execution should resume |
| `decisions.md` | Why the architecture is shaped the way it is |
| `analysis.md` | Codebase map for the current task (Gemini writes) |
| `plan.md` | Ordered execution steps (Claude Code writes) |
| `handoff.md` | Completion summary for the next tool (Codex writes) |

The first four files are permanent authored context. The last three are **baton files** — ephemeral per task, overwritten each cycle.

**Baton Integrity:** Every `plan.md` must carry a `TASKS_CHECKSUM` header. If the checksum of the current `tasks.json` differs from the plan header, the plan is stale and must be re-derived before execution proceeds.

---

## 7. Control plane responsibilities

The control plane exists to do three jobs only:

1. Reflect approved state  
2. Provide visibility  
3. Enforce boundaries  

The dashboard should remain intentionally narrow. For a proven V1 cycle, the essential tabs are **Tasks**, **Blueprint**, **Decisions**, **Session Log**, and **Actions**. The full 10-tab design is correct for the mature system but secondary until the full loop works reliably.

Expanding the UI surface too early increases maintenance cost without increasing system trust.

The **Actions** tab is especially important because it is where human authority remains explicit. If the system ever loses that boundary, it stops being an operating system and becomes an uncontrolled automation stack.

---

## 8. Agent model

There are two categories of agents in this system, and the distinction must stay sharp.

**External conversational agents** help think, design, decompose, and guide. They are structured thinking tools. In V1 they produce files and instructions, not direct writes. In V2 they write to the database via API after the local loop is proven.

The four core thinking agents:

| Agent | Output |
| :--- | :--- |
| Architect GPT | Designs features → `project.md` |
| Spec Gate GPT | Breaks work into tasks → `tasks.json` |
| Strategist GPT | Makes architectural decisions → `decisions.md` |
| Operator GPT | Manages sessions and continuity → `session.md` |

**Auxiliary agents (Specialists)** provide on-demand expertise (Backend, Database, Schema, Senior Dev, System Design, UI, and Auxiliary Strategist). They produce date-stamped proposal files for Architect review. They never finalize decisions or author requirements.

**Internal system agents** are execution playbooks or orchestrated roles with limited permissions. Their outputs are proposals, not facts, until approved through `ProposedAction`. This difference is a core part of the architecture.

The system is not just trying to use AI. It is trying to govern AI-assisted execution. Governance requires boundaries, permissions, and review points.

---

## 9. Tool strategy — the full stack

The system is composed of seven tool categories with separate budgets and defined roles.

### Claude Code — primary power tool

Weekly token limit. Used surgically. Full planning and complex builds. Multi-file reasoning and system architecture. Hard debugging where location is unknown. Enters plan mode before every task. Self-verifies before reporting completion. Opens with context loaded — never cold opens. Closes after each task — never left open between tasks.

**Claude Code boundary in PDOS:**

Claude Code does not author requirements. Claude Code does not produce `tasks.json`. Claude Code does not make architectural decisions.

Claude Code reads `tasks.json` (Spec Gate output) and `analysis.md` (Gemini output) to produce `plan.md`. Requirements come ONLY from `tasks.json`. analysis.md provides WHERE in the codebase — not WHAT to build. If they conflict, `tasks.json` wins.

Claude Code writes internal session tracking to `~/.claude/tasks.json` (ses-YYYYMMDD-NNN format only). These session tasks never enter the PDOS pipeline and never become TASK-001 entries without routing through Architect → Spec Gate.

**Staleness Detection:** Claude Code refuses to execute from a `plan.md` if the `TASKS_CHECKSUM` does not match the current `tasks.json`.

### Gemini CLI — primary fallback and context feeder

Free budget. Reads entire codebase in one shot — up to 1M token context. Produces `analysis.md` before Claude Code opens so Claude Code skips re-reading files. Covers planning and complex reasoning when Claude Code budget runs out. Picks up from `handoff.md` seamlessly when fallback is triggered.

### Codex — controlled execution

Separate budget. Executes one step at a time from `plan.md`. Minimal changes — only listed files. No assumptions — stops if unclear. Produces `handoff.md` after each step. Replaces Claude Code babysitting of simple execution.

### Cursor — UI and file editing

Separate budget. UI and frontend work. Single-file editing and refactoring. Adding tests to existing code. Linting and cleanup within files. Reads `.cursor/rules/` automatically. Same context source as Claude Code via shared `.claude/context/`.

### OpenCode — automation layer

Separate budget. Automates proven repeatable workflows only. Never used before manual execution is proven. Replaces Codex loops for validated task patterns. Automation is earned, not assumed.

### Kiro — optimization layer

Separate budget. Cleanup and polish after features are complete. Performance improvements on working code. Never used for core logic — speed not precision. Always runs after Claude Code finishes building.

### Four GPT agents — thinking layer

ChatGPT budget. Handle all design conversation before Claude Code opens. Claude Code receives decisions, not questions. Design, plan, decide, manage sessions.

### `agents push` — sync layer

Ties everything together. Syncs disk to SQLite after every session. Regenerates `CLAUDE.md` and `.cursor/rules/`. Updates dashboard state. Runs after every task completion and every session close.

---

### The baton system

Tools hand off via baton files, not re-reading source. No tool re-reads what a previous tool already read.

1. Gemini CLI writes `analysis.md`
2. Claude Code reads `analysis.md` (skips codebase)
3. Claude Code writes `plan.md` (with `TASKS_CHECKSUM`)
4. Codex reads one step from `plan.md`
5. Codex writes `handoff.md`
6. Operator GPT reads `handoff.md`
7. Gemini CLI reads `handoff.md` if fallback is needed

---

### Tool role declarations

**Claude Code:** "I am the primary power tool. I run at full power. Before you opened me: Gemini CLI analyzed the codebase → read analysis.md. Read analysis.md and plan.md first. Enter plan mode before every task. Self-verify before reporting complete. Write handoff.md before closing."

**Cursor:** "I handle UI, frontend, and single-file work. Read your step from plan.md only. One step at a time. After completing your step: write handoff.md. If stuck: write block reason to handoff.md and stop."

---

### Boris principles (integrated into tool strategy)

- **Plan mode first** — ~80% of sessions start in plan mode (Shift+Tab twice in Claude Code terminal). Full thinking before any building. Plan approved before first file is written.
- **Minimal CLAUDE.md** — keep under 1500 tokens. If bloated: run `agents trim-claude`. Add rules only when the model gets something wrong. Never add rules pre-emptively.
- **Self-verification** — Claude Code runs verification before reporting done. Human provides supplementary evidence only when Claude Code cannot self-verify.
- **Parallel sessions** — V2 concern after first three cycles proven. Keep WIP = 1 for V1.
- **Inner loop skills** — discover after first cycle, not before. Build skills only for patterns that repeat more than twice. Core skills after first cycle: `/session-start`, `/session-end`, `/task-start`, `/task-done`.
- **Build for the future** — context quality is the right investment. Every long prompt is a signal of missing context — move it to `.claude/context/` permanently.

---

## 10. The role of `agents init`

`agents init` is not a convenience script. It is the onboarding entry point to the operating system. Its job is to take a repo and make it system-ready in a repeatable, low-risk way.

Because it carries that much responsibility, it should not remain a single opaque script with many side effects. It should be decomposed into focused steps:

### Step 1: `init_bundle.sh`

- Creates `.claude/context/` with all template files  
- Copies `user.md` and `preferences.md` from global memory  
- Creates empty baton templates: `analysis.md`, `plan.md`, `handoff.md`  

### Step 2: `init_tools.sh`

- Generates `CLAUDE.md` (two-section structure)  
- Generates `.cursor/rules/00-context.mdc`  
- Creates `~/.cursor/rules/00-global.mdc` once if missing  

### Step 3: `init_docs.sh`

- Generates `.claude/docs/` with all 10 tab specs  
- One complete requirement contract per tab  

### Step 4: `init_register.sh`

- Updates `projects_index.json` (both copies)  
- Creates SQLite project row via `POST /api/projects`  

### Step 5: `init_validate.sh`

- Verifies all files exist  
- Prints clear status report  
- Fails loudly on missing items  

### Step 6: `agents push`

Runs automatically after the above when appropriate.

A strong `agents init` design must be:

- **Idempotent** — safe to re-run  
- **Verbose** — clear about what it created and what it skipped  
- **Recoverable** — able to retry failed phases without repeating everything  
- **Conservative** — never silently overwriting authored project files  

---

## 11. Real-world constraints

### 11.1 You are a solo operator

Major advantage — reduces auth, collaboration, and tenant concerns in V1. Also a trap if you overbuild for a future product before proving the local loop. Optimize for solo reliability first.

### 11.2 The infrastructure is ahead of the agents

The near-term priority is not maximum automation. It is stability in the dashboard, workers, sync boundaries, context model, and tool routing discipline.

### 11.3 Manual handoffs are acceptable in V1

Manual push is not failure in V1. It is a valid control strategy while the pipeline hardens. Remove manual steps only after the underlying state model is trustworthy.

### 11.4 SQLite is acceptable for the target stage

For a solo local-first control plane, SQLite is a good fit. Simple deployment, low operating cost, easy to back up. The risk is not scale. The risk is inconsistency between disk and database.

### 11.5 Claude Code has a weekly token limit

Running out in three days is a routing problem, not a capacity problem. The fix is surgical discipline: Gemini CLI feeds context, GPT agents handle design, Codex handles simple execution, Cursor handles file edits, Kiro handles cleanup. Claude Code touches only what requires its full power.

### 11.6 Home directory organization affects maintainability, not product truth

A messy home directory creates confusion but is not the same as system architecture. The real product-critical cleanup is responsibility separation, not cosmetic folder cleanup.

### 11.7 VPS over AWS for V3

SQLite requires single-machine deployment. VPS at ~$5/month is the correct fit. AWS serverless breaks the SQLite architecture. AWS EC2 is functionally similar to a VPS at higher cost with little benefit for a solo operator.

---

## 12. Failure modes and risk register

### Context drift

When files, database, and tool adapters do not match, the system presents stale or misleading state. **Mitigation:** project context is the authored source, database is the approved mirror, adapters are thin pointers.

### Overloaded initialization

If project setup tries to do too much in one script, partial setup becomes common and hard to diagnose. **Mitigation:** split `agents init` into subcommands with clear validation between each.

### Scope creep during execution

Once execution expands beyond the done condition, task integrity collapses. **Mitigation:** treat done conditions as hard boundaries — overflow becomes new tasks, never additions to the current task.

### Multiple tasks in progress

Creates contaminated git state, weak attribution, and inaccurate dashboards. **Mitigation:** WIP = 1 is a debugging requirement, not a preference.

### Premature dashboard expansion

If you add many tabs before the loop is proven, the UI becomes a maintenance burden rather than a control plane. **Mitigation:** keep the essential five tabs until the cycle is proven.

### Confused ownership between files and database

If the database becomes a silent second authoring surface, the system becomes harder to reason about. **Mitigation:** define clearly what is authored on disk, what is mirrored, and what is approved operational state.

### Claude Code budget exhaustion

Running out of tokens mid-week halts work on the primary power tool. **Mitigation:** eliminate anti-patterns — cold opens, long design conversations, babysitting execution, doing cleanup, repeating proven workflows, leaving sessions open between tasks. Primary fallback is Gemini CLI reading the three baton files.

### Tool drift between Claude Code and Cursor

Two tools knowing different versions of the project context. **Mitigation:** both tools point to the same `.claude/context/` folder. No content is duplicated. Tool configs are thin pointers only.

### CLAUDE.md bloat

Too many rules cause the model to miss the critical ones. **Mitigation:** keep under 1500 tokens. `agents trim-claude` prunes on demand. Delete and regenerate from memory files if severely bloated.

---

## 13. Phased delivery strategy

### Phase 0: Stabilize the context model

Lock the project context schema. Define the three baton files. Make tool adapters thin. Clarify ownership between disk and database. Define the tool routing table.

**Exit criteria:** a new project can be onboarded without ambiguity. Gemini CLI, Claude Code, Cursor, and Codex all read from the same source.

### Phase 1: Prove the local execution cycle

Keep everything local. Use manual push. Use a small project — not DMRB or the agent OS itself. Validate that the dashboard, sync workers, task flow, baton handoffs, and execution rhythm all work end to end.

**Exit criteria:** one full cycle completes cleanly, with project truth, task state, decisions, session continuity, git discipline, and tool routing all intact. Claude Code budget lasts the full week.

### Phase 2: Reduce friction, not control

Add remote access through ngrok and API protection. Replace manual transfers only after the local state model is stable. Set `ANTHROPIC_API_KEY`. Enable `task_worker` on schedule. Connect GPT agents to API via custom actions. Inner loop skills built from patterns discovered in Phase 1.

**Exit criteria:** agents can read and write through controlled API calls while the laptop is available, with no loss of approval boundaries.

### Phase 3: Always-on deployment

Move the execution layer to a VPS (e.g. Hetzner or DigitalOcean). Add HTTPS via Let's Encrypt, daily SQLite backup, systemd service supervision, Nginx reverse proxy, API key middleware. Treat deployment as an operations problem, not just a hosting problem.

**Exit criteria:** the control plane stays healthy without the laptop and supports remote continuity from phone to desk.

---

## 14. Folder and responsibility model

The right long-term structure is responsibility-based.

**Projects own:**

- Project context (`.claude/context/`)
- Tool entry files (`CLAUDE.md`, `.cursor/rules/`)
- Tab documentation (`.claude/docs/`)

**Shared runtime owns:**

- API, workers, dashboard, CLI logic
- SQLite database
- Logs and state

**Shared scaffold owns:**

- Reusable templates only
- `init.sh` and sub-scripts

**Global config owns:**

- Operator-wide memory and preferences
- Global `CLAUDE.md` and `.cursor/rules/`
- `~/.claude/memory/`

No layer tries to own another layer's truth. Once that happens, updates become fragile.

---

## 15. Implementation guidance for the next build cycle

The next cycle should not start with new features. It should start with structural hardening.

1. Execute home directory migration — approved and ready  
2. Fix the three broken things:  
   - `db.py` hardcoded path → `Path.home()`  
   - `decision_reviewer` cron → `python3.13`  
   - `agents push` → reads from `.claude/context/`  
3. Redesign `agents init` into five subcommands  
4. Add baton file templates to `agents init` output  
5. Add `agents trim-claude` command  
6. Build dashboard Session 1 — schema migrations and API routes  
7. Run first complete cycle on one small project  
8. Discover inner loop patterns — build skills after cycle  
9. Prove budget lasts full week before adding V2 features  

This order attacks ambiguity before adding convenience.

---

## 16. What makes this system valuable

The value is not just that it stores tasks or helps write code. The value is that it creates a disciplined bridge from idea to execution without relying on memory, chat history, or manual re-explanation. It preserves continuity, makes state legible, and constrains AI-assisted work inside a system you can inspect and trust.

It also solves the multi-tool coordination problem that most AI development workflows ignore. By routing work deliberately across a budget-conscious tool stack, it makes expensive tools last longer and cheaper tools earn their place. The baton system — `analysis.md` → `plan.md` → `handoff.md` — means no tool re-reads what another tool already processed.

In practical terms: less startup cost each session, fewer repeated explanations, better task quality, cleaner git behavior, fewer scope leaks, a system that can brief multiple tools consistently, and a weekly Claude Code budget that lasts all seven days.

---

## 17. Final strategic position

This system should be treated as a **context-driven execution OS** with a human-governed control plane and a deliberate multi-tool routing strategy.

That framing resolves most of the design questions.

- Context lives in `.claude/context/`, not in tool configs.  
- The database is for **approved operational state**, not authoring.  
- Tools integrate via **thin pointers** to shared context, not duplicated stacks.  
- Approval boundaries exist for **governance**, not restriction.  
- V1 must be proven locally before adding remote convenience.  
- Claude Code is the **primary power tool**, not the default for everything.  
- Gemini CLI is both **context feeder** and **fallback**, keeping the system resilient when the primary tool runs out.  

The strongest version of the system is not the most automated version. It is the version with the clearest ownership, the fewest hidden assumptions, the highest confidence that what the system shows is actually true, and the most disciplined routing of work to the right tool at the right cost.

That is the standard to build toward.

---

## Appendix A — System invariants

Rules that never change at any version.

1. Files are the source of truth. DB is the mirror.  
2. No task is done until merged, pulled, and human-confirmed.  
3. No agent writes directly to tasks, blueprints, or decisions.  
4. All agent writes pass through `ProposedAction`.  
5. Blueprint and Decisions are read-only in the dashboard.  
6. WIP limit is 1. One task in progress at all times.  
7. Every task has a testable done condition before execution starts.  
8. Verification must pass before commit gate opens.  
9. `session.md` is written at the end of every session without exception.  
10. V1 proven before V2. V2 proven before V3. No skipping.  
11. Never optimize prompts. Optimize context.  
12. Every long prompt signals missing context — move it to `.claude/context/`.  
13. Analyze before planning. Plan before executing. Unclear analysis means stop — not proceed with assumptions.  
14. Minimal changes only. Only listed files. No assumptions. One step at a time. Never batch steps.  
15. Never automate a step that has not been manually verified first.  
16. `CLAUDE.md` must stay under 1500 tokens.  
17. Claude Code runs at full power. Zero waste. Lasts the full week.  
18. Every Claude Code session opens with context loaded. Zero cold opens.  
19. Claude Code plans and builds. It does not babysit execution or cleanup.  
20. Gemini CLI is the fallback. Feed it the baton files. Work continues.  
21. Tools hand off via baton files. No tool re-reads what another already read.  
22. OpenCode is earned. Automate only after manual execution is proven.  
23. `plan.md` must match `tasks.json` checksum. No execution from stale plans.

---

## Appendix B — Tool routing table

| Work type | Tool | Budget |
| :--- | :--- | :--- |
| Read and analyze codebase | Gemini CLI | Free |
| Find connections and risks | Gemini CLI | Free |
| Produce `analysis.md` | Gemini CLI | Free |
| Fallback planning | Gemini CLI | Free |
| Design features | Architect GPT | ChatGPT |
| Break into tasks | Spec Gate GPT | ChatGPT |
| Make decisions | Strategist GPT | ChatGPT |
| Session management | Operator GPT | ChatGPT |
| Complex planning and builds | Claude Code | Weekly reserved |
| Multi-file reasoning | Claude Code | Weekly reserved |
| Hard debugging | Claude Code | Weekly reserved |
| System architecture | Claude Code | Weekly reserved |
| Simple step execution | Codex | Separate |
| Single file changes | Codex | Separate |
| Minimal targeted edits | Codex | Separate |
| UI and frontend work | Cursor | Separate |
| File editing in IDE | Cursor | Separate |
| Tests and linting | Cursor | Separate |
| Proven repeatable automation | OpenCode | Separate |
| Cleanup and optimization | Kiro | Separate |
| Polish after feature complete | Kiro | Separate |
| **Specialist: Backend** | Backend Specialist | ChatGPT (proposal) |
| **Specialist: Database** | Database Specialist | ChatGPT (proposal) |
| **Specialist: Schema** | Schema Specialist | ChatGPT (proposal) |
| **Specialist: Senior Dev** | Senior Dev | ChatGPT (proposal) |
| **Specialist: System Design**| System Design | ChatGPT (proposal) |
| **Specialist: UI** | UI Specialist | ChatGPT (proposal) |
| **Specialist: Advisor** | Aux Strategist | ChatGPT (proposal) |

---

## Appendix C — Weekly budget design

**Target:** ~14% of Claude Code weekly budget per day.

| Day | Allocation |
| :--- | :--- |
| **Monday** | Gemini + GPT agents: analysis and design. Claude Code: heavy planning (~14%). |
| **Tuesday** | Codex and Cursor: execution. Claude Code: complex builds (~14%). |
| **Wednesday** | Claude Code: architecture and hard problems (~14%). OpenCode: proven automations. Cursor: file edits. |
| **Thursday** | Claude Code: complex debugging (~14%). Kiro: optimize completed features. |
| **Friday** | Claude Code: final verification and close (~14%). Kiro: cleanup pass. Operator GPT: week-closing `session.md`. `agents push`: full state sync. |
| **Weekend** | ~14% buffer — emergency or rolls to next week. |

---

## Appendix D — Fallback protocol

When Claude Code runs out mid-week:

1. **Switch to Gemini CLI immediately.** Do not stop working.

2. **Feed Gemini the baton files**, for example:

   ```text
   gemini "Read:
     .claude/context/analysis.md
     .claude/context/session.md
     .claude/context/plan.md
     .claude/context/handoff.md
   You are taking over from Claude Code.
   Continue from where it stopped."
   ```

3. **Continue with full stack:**

   - Gemini CLI → complex planning  
   - Codex → step execution  
   - Cursor → file edits and UI  
   - OpenCode → proven automations  
   - Kiro → cleanup  

4. **Log the fallback in `decisions.md`**, e.g.  
   *Claude Code ran out [date]. Switched to Gemini CLI. Anti-pattern that caused burnout: [identify].*

5. **Post-mortem next Monday** — adjust routing discipline to prevent repeat.
