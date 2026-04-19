# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What this repository is

MGPOD is a **pure documentation repository** — no application code, no build system, no tests. Every file is a Markdown prompt, knowledge rule, or JSON schema that governs how a Personal Developer OS (PDOS) operates. There are no commands to run here. Changes are edits to `.md` and `.json` files only.

---

## Authority model (read before editing anything)

Every artifact has exactly one owner. Edits that violate ownership break downstream agents.

| Artifact | Sole authority |
|----------|----------------|
| `project.md` Section A + Section B | Architect GPT |
| `schema.json` | Architect GPT |
| `[project-root]/.claude/tasks.json` (TASK-001 format) | Spec Gate GPT |
| `session.md` | Operator GPT |
| `decisions.md` | Strategist GPT |
| `analysis.md` | Gemini CLI |
| `plan.md` | Claude Code (derived from tasks.json + analysis.md) |
| `handoff.md` | Codex |
| `proposal.md` (any variant) | Aux agents — non-authoritative, advisory only |
| `~/.claude/tasks.json` (ses-YYYYMMDD-NNN format) | Claude Code (session tracking only) |

Claude Code reads `[project-root]/.claude/tasks.json` (Spec Gate output) but **never writes to it**.

---

## Document map

### Start here
- `Agent documentation/tier-1/master-document.md` — canonical system design, tool routing, invariants
- `Shared documents/core-agents-contracts/system_contract.md` — pipeline rules shared by all four agents
- `Official agents/README.md` — where official vs legacy agent folders live
- `Official agents/core/architect/vertical-data-flow.md` — Mermaid diagrams of the full 7-layer stack

### Agent system prompts (load these into ChatGPT)
- `Official agents/core/architect/agent-architecture-official/prompt/architect.md` — Architect GPT
- `Official agents/core/execution-spec-gate/agent-architecture-official/prompt/spec_gate.md` — Execution Spec Gate GPT
- `Shared documents/core-agents-contracts/` — shared contracts (requirement_contract, system_contract, user_profile, claude_code_contract)

### Knowledge trees (agent-specific rules)
- `Official agents/core/architect/agent-architecture-official/knowledge/` — 9 files (requirement_contract, validation, questioning_rules, invariants, etc.)
- `Official agents/core/execution-spec-gate/agent-architecture-official/knowledge/` — 10 files (input_validation, task_generation, task_spec, translation_rules, description_template, dependency_rules, infrastructure_rules, gap_handling, failure_modes, invariants)
- `Shared documents/auxiliary-agents/` — 4 files governing auxiliary proposal agents (system_rules, proposal_schema, initialization_protocol, enforcement_rules)

### Specialist agents (7 under `Official agents/auxiliary/`, same tree each)
- `Official agents/auxiliary/[role]/agent-architecture-official/prompt/[role].md` — system prompt
- `Official agents/auxiliary/[role]/agent-architecture-official/knowledge/` — 5 files: responsibilities, domain_rules, boundaries, proposal_contract, failure_modes
- `Legacy agents/auxiliary/[role]/agent-architecture-legacy/legacy-prompt/` and `legacy-knowledge/` — retired material only (do not load as canonical)
- Auxiliary Strategist uses the same official/legacy layout under `Official agents/core/strategist/` (prompt `strategist.md`) for **official**; legacy under `Legacy agents/core/strategist/`

### Tiered operational docs
- `Agent documentation/tier-1/` — specs, registry, framework
- `Agent documentation/tier-2/` — dashboard, SQLite, sync layer, workers
- `Agent documentation/tier-3/` — OS, ChatGPT thinking layer, Blueprint
- `Agent documentation/tier-4/` — Claude Code, Codex, Gemini CLI, Kiro, OpenCode

---

## Core pipeline (locked)

```
User → Architect GPT → Spec Gate GPT → [tasks.json] → Operator GPT → Claude Code → Git

Aux agents (7 specialists) → proposal.md → Architect GPT (validates) → Section A/B
Strategist GPT → decisions.md (on-call, not sequential)
Gemini CLI → analysis.md → Claude Code → plan.md → Codex → handoff.md
```

The pipeline has one direction. No agent feeds Spec Gate directly except Architect. No agent authors tasks.json except Spec Gate.

---

## The two tasks.json files (never confuse these)

| File | Schema | Producer | Claude Code access |
|------|--------|----------|--------------------|
| `[project-root]/.claude/tasks.json` | `TASK-001` format, 12 keys | Spec Gate GPT only | Read-only |
| `~/.claude/tasks.json` | `ses-YYYYMMDD-NNN` format, 9 keys | Claude Code (session tracking) | Read-write |

The schemas are in:
- TASK-001: `Legacy agents/core/execution-spec-gate/agent-architecture-legacy/legacy-knowledge/tasks_schema.json`
- ses-: governed by `~/.claude/CLAUDE.md`

---

## Section B format (required — Spec Gate blocks anything else)

Architect must produce Section B with exactly these 10 headings in order:
`PROJECT` · `TYPE` · `ARCHITECTURE` · `CRITICAL CONSTRAINTS` · `MVP SCOPE` · `OUT OF SCOPE` · `REQUIREMENTS` · `FILE STRUCTURE` · `CURRENT STATE` · `NEXT`

Each `REQ-###` must have: `Trigger → Output | done when: [testable] | fails: [behavior]`

---

## proposal.md conventions

Aux agents must use date-stamped filenames: `proposal_[YYYYMMDD]_[agent-role].md`

Every proposal.md must carry a Status header:
```
**Status:** PROPOSED | UNDER REVIEW | PROMOTED | REJECTED
**Reviewed by Architect:** [date, or PENDING]
```

The 8 required sections (heading must match exactly): Scope · Decisions · Options (A/B/C) · Constraints · Risks · Invariants · System Impact · Open Questions

Forbidden inside proposal.md: REQ-IDs, `Done when:`, `tasks.json` fragments, numbered execution steps, language implying Spec Gate or Operator must run next.

---

## Editing rules

- `Official agents/core/execution-spec-gate/agent-architecture-official/knowledge/` and `Official agents/core/architect/agent-architecture-official/knowledge/` are loaded verbatim into GPT agents. Changes here change agent behavior immediately.
- `Shared documents/core-agents-contracts/system_contract.md` is shared across all four agents. Edits here must be consistent with all four agent prompts.
- `Shared documents/auxiliary-agents/system_rules.md` governs all 7 specialist agents. A rule added here applies to all of them.
- Legacy docs under `Legacy agents/**/agent-architecture-legacy/` are archived reference — do not update them; update the official knowledge files under `Official agents/` instead.
- `Official agents/core/architect/vertical-data-flow.md` contains Mermaid diagrams. Update diagrams when pipeline structure changes.
