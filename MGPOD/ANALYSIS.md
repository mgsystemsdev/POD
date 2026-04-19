# MGPOD System Analysis: Principal Systems Analyst Report

This report provides a deep-dive analysis of the **MGPOD (Personal Developer Operating System)**, a context-driven execution framework designed for high-discipline, AI-assisted software delivery.

---

## 1. Executive Synthesis

**MGPOD** is not a project management tool; it is a **governance-first execution environment**. It addresses the "context-drift" and "token-burn" problems inherent in modern AI development by decoupling **thinking** (requirements/architecture) from **doing** (execution/coding).

### Core Mental Model: The "Baton" Pipeline
The system operates as a **unidirectional, human-gated pipeline**. High-level intent is refined through a series of "Baton Files" that ensure no tool ever works "cold" or re-reads what a previous tool already processed.

**The Diagram (Prose):**
Imagine a vertical stack where **Thinking Agents** (ChatGPT) sit at the top, producing a immutable **Project Truth** (Layer 2 - Disk). This truth is mirrored into an **Operational Control Plane** (Layer 4 - SQLite), which provides visibility via a **Dashboard**. **Execution Tools** (Claude Code, Cursor) then "check out" a single task, grounding themselves in the shared disk context before committing code to **Version Control** (Layer 7).

---

## 2. Authority & Ownership Map

The system enforces a strict **Sole Authority** model to prevent state contamination. Violating this map is the primary cause of system failure.

> **Strategist disambiguation:** "Strategist GPT" below = **Pipeline Strategist** (GPT-3, on-call during execution, produces canonical `decisions.md`). This is different from the **Auxiliary Strategist** at `Official agents/core/strategist/` (on-demand advisor, produces advisory `proposal.md`).

| Artifact Class | Sole Writer | Primary Reader(s) | Forbidden Writer |
| :--- | :--- | :--- | :--- |
| `.claude/blueprint/` (9 docs) | **Blueprint Creator** | Architect GPT (MODE 0) | All others |
| `project.md` §A/§B | **Architect GPT** | Spec Gate, Operator, Pipeline Strategist | All others |
| `schema.json` | **Architect GPT** | Spec Gate, Operator, Pipeline Strategist | All others |
| `tasks.json` (TASK-001) | **Spec Gate GPT** | Operator GPT, Claude Code (Read) | **Claude Code** |
| `decisions.md` | **Pipeline Strategist GPT** | Operator GPT, Architect | All others |
| `session.md` | **Operator GPT** | Operator (next session) | Claude Code |
| `analysis.md` | **Gemini CLI** | Claude Code | All others |
| `plan.md` | **Claude Code** | Codex, Cursor | All others |
| `handoff.md` | **Codex / Cursor** | Operator GPT, Gemini CLI | All others |
| `proposal.md` | **Aux Agents** | Architect GPT | All others |
| `~/.claude/tasks.json` | **Claude Code** | Claude Code | Spec Gate |

---

## 3. End-to-end Pipelines

### A. The Requirement-to-Code "Main Thread"
0.  **Blueprint Creator → Architect**: User provides any idea; Blueprint Creator produces a nine-document draft bundle. Architect reads bundle in MODE 0 — BUNDLE IMPORT (if bundle is provided) or directly from user input. Bundle is draft only — not canonical.
1.  **Architect → Spec Gate**: Architect produces a requirement contract (Trigger/Input/Output/Constraints/Failure). Spec Gate validates the 5-element contract and generates an atomic `tasks.json`.
2.  **Spec Gate → SQLite**: The `import_worker` ingests `tasks.json` into the database, where tasks appear on the Dashboard.
3.  **Human → Operator**: Miguel approves a task on the Dashboard.
4.  **Operator → Claude Code**: Operator briefs Claude Code on the current task and session context.
5.  **Claude Code → Git**: Claude executes the change, self-verifies, and commits to a task-specific branch.

### B. The Context-Optimization "Baton" Flow
1.  **Gemini CLI**: Reads the entire codebase (1M+ context) and produces `analysis.md` (the "WHERE").
2.  **Claude Code**: Reads `tasks.json` (the "WHAT") and `analysis.md`. Produces `plan.md`.
3.  **Codex**: If the step is simple, Codex reads `plan.md` and produces `handoff.md`.

---

## 4. Invariants & Non-negotiables

-   **WIP = 1**: Only one task may be in progress at any time to prevent git contamination.
-   **Human Approval at State Boundaries**: No requirement becomes a task, and no code is merged to `main`, without explicit human confirmation.
-   **The `ses-` vs `TASK-` Partition**: Claude Code **must never** write to project-root `tasks.json`. It only writes session tasks to its internal `~/.claude/tasks.json`.
-   **No Cold Opens**: Claude Code never opens a project without loading `.claude/context/` first.
-   **Verification Priority**: A task is not "done" based on AI claims; it is done when the `success_criteria` (derived from requirement Output) is empirically verified.

---

## 5. Layered Architecture

MGPOD is structured into **7 Layers**, moving from abstract thought to concrete bits:

1.  **Layer 1 (Thinking)**: External GPT agents (Architect, Spec Gate).
2.  **Layer 2 (Knowledge)**: Disk-based `.claude/context/` (Authored Truth).
3.  **Layer 3 (Sync)**: `agents push` logic mirroring disk to DB.
4.  **Layer 4 (Data)**: SQLite mirror (Operational Truth).
5.  **Layer 5 (Control Plane)**: FastAPI Dashboard & Workers.
6.  **Layer 6 (Execution)**: Claude Code, Gemini, Codex.
7.  **Layer 7 (VC)**: Git history and branch management.

---

## 6. Tool-routing & Token Economics

The system routes work to the **cheapest capable tool** to preserve the Claude Code weekly budget:
-   **Gemini CLI**: Used for massive codebase analysis (Free/Large Context).
-   **Claude Code**: Reserved for **complex builds** and **multi-file reasoning**.
-   **Codex**: Used for executing **simple, documented steps** from `plan.md`.
-   **Kiro**: Handles **cleanup and polish** only *after* a feature is complete.
-   **GPT Agents**: Handle **conversational design** (ChatGPT budget).

---

## 7. Contracts & Knowledge Trees

The **Requirement Contract** is the atomic unit of the system. It *must* contain:
-   **Trigger**: What starts the behavior?
-   **Input**: Valid/Invalid data and rejection cases.
-   **Output**: Observable result + Verification method.
-   **Constraints**: Checkable limits (performance, volume).
-   **Failure Path**: Retries, state handling, and blast radius.

This contract propagates directly into the `tasks.json` `success_criteria` and `failure_behavior` fields, ensuring the Developer knows exactly how to prove completion.

---

## 8. Failure Modes & Anti-patterns

-   **"Cold Open"**: Starting a session without reading `analysis.md` or `session.md`. Result: AI guesses the state and creates drift.
-   **"Silent Production Bug"**: A generic Failure path in the PRD (e.g., "log error") leads to unhandled edge cases in code.
-   **"Schema Drift"**: `schema.json` is updated but Section A is not. Result: Spec Gate generates tasks against an old model.
-   **"Bypassing the Gate"**: Manually adding tasks to `tasks.json` without Architect review. Result: Unreliable `done when` conditions.

---

## 9. Internal Consistency Check

**Conflict Found & Resolved**: The "Two `tasks.json` Files" collision. 
-   **Status**: RESOLVED. 
-   **Logic**: `~/.claude/tasks.json` (Session tasks, `ses-` prefix) is owned by Claude Code. `[project]/.claude/tasks.json` (Project tasks, `TASK-` prefix) is owned by Spec Gate. Claude Code may **read** the latter but never **write** to it.

**Conflict Found & Resolved**: `plan.md` source of truth.
-   **Logic**: `plan.md` requirements come **exclusively** from `tasks.json`. `analysis.md` provides navigation context only. If they conflict, `tasks.json` wins.

---

## 10. Gaps & Research Debt

1.  **Stale `plan.md` Detection**: If Spec Gate regenerates `tasks.json` while Claude has a `plan.md` open, there is no automated signal to re-derive the plan.
2.  **Automated Enforcement**: The `ses-` vs `TASK-` rule is currently a "soft" prompt-based rule. It needs a git-hook or pre-tool check to prevent accidental writes by AI.
3.  **Proposal Versioning**: `proposal.md` files lack a central registry; multiple specialist agents might overwrite each other's proposals if not date-stamped.

---

## 11. Stress Tests (Behavioral Analysis)

**Scenario A: Aux agent promotes a proposal violating Section B.**
-   **Correct Behavior**: Architect GPT must run in **PRD UPDATE** mode, read the proposal, compare it against Section B invariants, and **BLOCK** the promotion, asking Miguel for a reconciliation decision.

**Scenario B: Claude edits project-root `tasks.json`.**
-   **Correct Behavior**: The `import_worker` or `sync_worker` should detect a non-Spec Gate signature or a `ses-` prefix in the project root and **Reject the sync**, flagging "Authority Violation" on the Dashboard.

**Scenario C: `session.md` and `plan.md` disagree.**
-   **Correct Behavior**: Operator GPT must read `session.md` at session start. If `plan.md` suggests Task X but `session.md` says Task X was completed, the Operator must **STOP**, delete `plan.md`, and re-invoke Claude Code to read the *current* state.

---

## Final Finding for `analysis.md`
The MGPOD system is functionally closed but relies heavily on **human enforcement of agent boundaries**. The transition from V1 (Manual) to V2 (API) will be the most dangerous phase, as the risk of agents "correcting" each other's files increases.

**Recommendation (Non-canonical):**
Implement a **`system_monitor`** worker that runs on every `agents push` specifically to check file modification timestamps against the **Authority Map**. If a forbidden agent (e.g., Claude Code) is the last modifier of an Architect-owned file, the sync must fail loudly.
