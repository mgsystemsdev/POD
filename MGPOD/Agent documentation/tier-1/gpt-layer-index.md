# GPT layer index

Single-page reference for the full PDOS GPT layer: five core pipeline roles + seven auxiliary agents. Read this before opening any agent prompt.

---

## TWO STRATEGISTS — DISAMBIGUATION NOTICE

This system has two agents with "Strategist" in their role. They have different authority levels and different locations.

| | Pipeline Strategist | Auxiliary Strategist |
|---|---|---|
| **Position** | GPT-3 of 5 — on-call during execution | On-demand advisory specialist |
| **Output** | `decisions.md` — canonical | `proposal_[YYYYMMDD]_[agent-role].md` — advisory only |
| **Prompt** | `Shared documents/core-agents-contracts/pipeline_strategist.md` | `Official agents/core/strategist/agent-architecture-official/prompt/strategist.md` |

Never confuse the two.

---

## Core pipeline (five roles, sequential + one on-call)

| Role | Artifact produced | Hard boundary | Entrypoint |
|------|-------------------|---------------|------------|
| **Blueprint Creator (GPT-0)** | Nine-document draft bundle at `[project-root]/.claude/blueprint/` | No canonical artifacts — draft only | `Official agents/core/blueprint-creator/agent-architecture-official/prompt/blueprint_creator.md` |
| **Architect (GPT-1)** | `project.md` (Sec A + B) + `schema.json` | No tasks, no code, no library picks | `Official agents/core/architect/agent-architecture-official/prompt/architect.md` |
| **Execution Spec Gate (GPT-2)** | `tasks.json` | No design, no invented requirements, no partial tasks | `Official agents/core/execution-spec-gate/agent-architecture-official/prompt/spec_gate.md` |
| **Pipeline Strategist (GPT-3, on-call)** | `decisions.md` entries — canonical | No task JSON, no execution, no design from scratch | `Shared documents/core-agents-contracts/pipeline_strategist.md` |
| **The Operator (GPT-4)** | `session.md` + committed code | No design, no task JSON, no strategic decisions | `Official agents/core/operator/agent-architecture-official/prompt/operator.md` |

**Flow:** User → Blueprint Creator → Architect → Spec Gate → [tasks.json → SQLite → Dashboard] → Operator ← Pipeline Strategist (on-call only)

Blueprint Creator output is draft only. The Architect validates it into `project.md` using MODE 0 — BUNDLE IMPORT.

All five core roles implement **Pattern 13 — Adaptive System Awareness**: detect the entry path first, announce it, read existing artifacts before asking new questions, then adapt behavior to that context.

---

## Auxiliary agents (seven, on-demand, advisory only)

All seven agents output **only** `proposal_[YYYYMMDD]_[agent-role].md`. No authoritative artifacts. Architect alone promotes proposal content into Section A / Section B / `schema.json`.

| Agent folder | Specialty | Proposal lens | Key cross-tension |
|--------------|-----------|---------------|-------------------|
| `Official agents/core/strategist/` | Scope framing, strategic posture, candidate invariants | What is the strategic posture? | vs Pipeline Strategist (different authority — see disambiguation above) |
| `Official agents/auxiliary/ui_specialist/` | User flows, interaction states, UX edge cases, accessibility | State machines, flow postures | vs backend_specialist on state authority |
| `Official agents/auxiliary/backend_specialist/` | API contracts, validation logic, failure paths | API boundary options | vs schema_specialist on normalization; vs ui_specialist on state truth |
| `Official agents/auxiliary/schema_specialist/` | Data model, relationships, normalization | Conceptual model postures | vs database_specialist on perf denorm; vs backend on aggregation |
| `Official agents/auxiliary/database_specialist/` | Indexing, performance, migrations | Storage/index postures | vs schema_specialist on normalization vs performance |
| `Official agents/auxiliary/system_design/` | Architecture patterns, service boundaries, integration design | Structural boundary postures | vs backend/database on service isolation vs coupling |
| `Official agents/auxiliary/senior_dev/` | Production realism, delivery risk, operational cost, failure modes | Will this survive production? | vs aux Strategist (ops/failure lens vs strategy lens) |

---

## Artifact map

```
User (any idea)
 │
 ▼
Blueprint Creator (GPT-0) ──────────────────► .claude/blueprint/ (9 documents, DRAFT ONLY)
 │                                                       │ MODE 0 — BUNDLE IMPORT
 ▼                                                       ▼
Architect (GPT-1) ──────────────────────────► project.md (Sec A+B) + schema.json
                                                        │ Section B only
                                                        ▼
                                          Spec Gate (GPT-2) ──► tasks.json
                                                        │
                                          [import worker → SQLite → Dashboard]
                                                        │
                                                        ▼
Pipeline Strategist (GPT-3, on-call) ◄──── Operator (GPT-4) ──► session.md
          │                                      │
          ▼                                      ▼
     decisions.md                      Claude Code (execution engine)
                                                 │
                                                 ▼
                                       plan.md → Codex → handoff.md → Git

Aux Strategist ──► proposal_[YYYYMMDD]_[agent-role].md ──► User ──► Architect (reviews/promotes)
Aux agents (6) ──► proposal_[YYYYMMDD]_[agent-role].md ──► User ──► Architect (reviews/promotes)
```

---

## Entrypoint paths — shared knowledge

| File | Purpose |
|------|---------|
| `Shared documents/core-agents-contracts/system_contract.md` | Pipeline definition, Section B schema, baton rules |
| `Official agents/core/architect/agent-architecture-official/knowledge/requirement_contract.md` | Five-element contract definition (Trigger, Input, Output, Constraints, Failure path) |
| `Shared documents/core-agents-contracts/pipeline_strategist.md` | Pipeline Strategist prompt (on-call during execution) |
| `Shared documents/auxiliary-agents/system_rules.md` | Authority table and global prohibitions for all aux agents |
| `Shared documents/auxiliary-agents/proposal_schema.md` | Mandatory eight-section structure + filename + Status block |
| `Shared documents/auxiliary-agents/initialization_protocol.md` | Ask → Load → Confirm → Proceed sequence (all aux agents) |
| `Shared documents/auxiliary-agents/enforcement_rules.md` | Self-check gate before any aux agent emits output |
| `Agent documentation/tier-3/chatgpt-agents-thinking-layer.md` | Overview of all pipeline GPT roles |
| `12patterns.md` | The thirteen design patterns — acceptance criteria for every agent |
