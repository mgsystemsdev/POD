# 5 ChatGPT agents (thinking layer)

## Overview

The **thinking layer** is five specialized ChatGPT agents: external cognitive partners for intake, design, task decomposition, strategy, and execution control **before** and during execution. They live outside the local stack to preserve Claude Code tokens and manage conversational context.

---

## System purpose

Eliminate **AI guessing** and **context drift**. Each agent exists so the operator does not build something they cannot maintain, explain, or trust.

---

## Layer 0 — Blueprint Creator (structured intake)

**Entry point** for raw ideas and existing builds that need to be turned into a structured nine-document draft bundle before the Architect hardens anything.

| Aspect | Detail |
| :--- | :--- |
| **Trigger** | Brand-new idea or existing build that needs structured documentation. |
| **Process** | Road A / Road B intake, one question at a time, nine-document bundle flow. |
| **Key deliverable** | Blueprint Creator bundle at `.claude/blueprint/` (draft only). |
| **Handoff** | Architect enters MODE 0 — BUNDLE IMPORT. |

---

## Layer 1 — The Architect (design and requirements)

**Entry point** for new projects and major features — the **what** and **how** of architecture.

| Aspect | Detail |
| :--- | :--- |
| **Trigger** | Raw idea or request for a design update. |
| **Process** | Recursive, one-question-at-a-time interview. |
| **Key deliverable** | AI-ready PRD (~14 sections: architecture, data models, rules, constraints). |
| **Other outputs** | Blueprint (Markdown), JSON spec (`schema.json`), file tree. |
| **Handoff** | Operator directed to the Execution Spec Gate. |

---

## Layer 2 — Execution Spec Gate (task decomposition)

**Specification gatekeeper** — turns design into executable units.

| Aspect | Detail |
| :--- | :--- |
| **Trigger** | Full PRD or Section B from the Architect. |
| **Process** | Single-pass: validate input → BLOCK (missing contract element) or ASK (ambiguity fork) or emit `tasks.json`. See `Official agents/core/execution-spec-gate/agent-architecture-official/prompt/spec_gate.md` for the operative definition. |
| **Output** | Atomic Markdown task blocks formatted for Python ingestion → SQLite dashboard. |
| **Constraints** | Dependency order; every task has a testable **done condition**. |

---

## Layer 3 — Pipeline Strategist (on-call advisory)

**Not** daily-use — a lifeline when execution stalls or the PRD is incomplete.

| Aspect | Detail |
| :--- | :--- |
| **Trigger** | Task blocked, missing PRD coverage, or confusing Claude Code output. |
| **Role** | Senior-dev style: current state vs PRD, architectural choices. |
| **Process** | Surface tensions; **three options** with trade-offs; recommendation. |
| **Output** | Decisions → `decisions.md`; translations and recommendations for execution decisions. |

> **Note:** The Pipeline Strategist (this layer) is a separate ChatGPT agent from the **`Official agents/core/strategist/` auxiliary agent**. The Pipeline Strategist produces authoritative `decisions.md` entries on-call during execution. The aux Strategist at `Official agents/core/strategist/` produces advisory `proposal_[YYYYMMDD]_strategist.md` only — reviewed by Architect before any content is promoted.

---

## Layer 4 — The Operator (execution engine)

**Driver** of terminal discipline — ship cleanly.

| Aspect | Detail |
| :--- | :--- |
| **Trigger** | Highest-priority task selected from the dashboard. |
| **Process** | Enforced cycle: Execute → Verify → Translate → Review → Commit → Next. |
| **Discipline** | Branch per task; PRs before merge; never work directly on `main`. |
| **Output** | Terminal commands, swarm prompts, mandatory `session.md` for continuity. |

---

## Core constraints and protocols

- **Plain English rule** — GPT translations of tool output: paragraphs only; **no** code blocks in those explanations.
- **Three-option protocol** — if the user is stuck, present exactly **three** options plus a recommended path.
- **Ecosystem awareness** — prompts include a **YOU ARE HERE** marker in the pipeline so agents do not steal each other’s jobs.
- **Authored vs operational** — agents produce **files** (truth); `agents push` mirrors to SQLite.

---

## Knowledge files by agent

| Agent | Primary knowledge files |
| :--- | :--- |
| **Blueprint Creator** | `pillar_definitions.md`, `pillar_sequence.md`, `handoff_protocol.md`, `plain_language_rules.md`, `tech_stack_guide.md`, `non_technical_user_guide.md`, `drift_control.md` |
| **Architect** | `user_profile.md`, `phase_guide.md`, `artifact_templates.md`, `questioning_patterns.md`, `schema.json` |
| **Spec Gate** | Self-contained (PRD is the input) |
| **Pipeline Strategist** | `user_profile.md`, `principles.md`, `tools_guide.md`, `claude_os_field_guide.pdf` |
| **Operator** | `user_profile.md`, `claude_os_operations.md`, `swarm_patterns.md` |

`user_profile.md` is shared across Blueprint Creator, Architect, Pipeline Strategist, and Operator for consistent stack and decision style.
