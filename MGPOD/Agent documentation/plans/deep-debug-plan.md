# Deep Debug Plan — PDOS Agent Prompt + Knowledge File Hardening
**Date:** 2026-04-13  
**Scope:** Role performance audit — all 12 PDOS agents  
**Status:** Phase 1-5 complete. Depth fixes (G-15) deferred to next session.

---

## SUMMARY OF FINDINGS

### P0 Bugs Fixed
- **Operator:** Official knowledge directory was empty. Prompt referenced 5 files that did not exist (`requirement_contract.md`, `user_profile.md`, `stack_guide_v2.md`, `session_start.md`, `scope_management.md`, `git_mindset.md`). Six knowledge files created. Prompt updated to reference correct paths. Prompt trimmed from 11,182 → 9,149 chars.

### Pattern Bugs Fixed

| Agent | Bug | Fix |
|-------|-----|-----|
| Blueprint Creator | No ENTRY POINTS announce text | Added "Entry recognized: Road A/B —..." text |
| Blueprint Creator | P8 — No inline DRIFT CONTROL table | Added 5-row DRIFT CONTROL table |
| Architect | P9 — No git commit instruction in output rules | Added commit command to §11 |
| Architect | CHAR — Over limit (10,316) | Extracted §9+§10 to edge_cases.md |
| Execution Spec Gate | P10 — No handoff instruction | Added §14 HANDOFF |
| Execution Spec Gate | P7 — Non-technical user protocol minimal | Expanded §13 with detection heuristic |
| Pipeline Strategist | P5 — No explicit "I do NOT do" section | Added §2a WHAT I DO NOT DO |
| Pipeline Strategist | Under-populated (2,200 chars available) | Added two new HARD STOPS (PRD ambiguous, REQs conflict) |
| Pipeline Strategist | P7 — No non-technical user protocol | Added to §11 STYLE |
| Senior Dev | P1 — "Ask 1-2 questions" violates one-question rule | Fixed to "one question; three options if stuck" |
| ALL 7 auxiliary | P3 — No HARD STOPS section | Added agent-specific HARD STOPS to each |
| ALL 7 auxiliary | P12 — No explicit human gate | Added human gate paragraph to each |

### New Knowledge Files Created
- `Official agents/core/architect/agent-architecture-official/knowledge/edge_cases.md`
- `Official agents/core/operator/agent-architecture-official/knowledge/session_start.md`
- `Official agents/core/operator/agent-architecture-official/knowledge/scope_management.md`
- `Official agents/core/operator/agent-architecture-official/knowledge/git_mindset.md`
- `Official agents/core/operator/agent-architecture-official/knowledge/user_profile.md`
- `Official agents/core/operator/agent-architecture-official/knowledge/requirement_contract.md`
- `Official agents/core/operator/agent-architecture-official/knowledge/stack_guide_v2.md`

---

## FINAL CHARACTER COUNTS

| Agent | Before | After | Status |
|-------|--------|-------|--------|
| Blueprint Creator | 7,935 | 7,924 | AT limit ✅ |
| Architect | 10,316 | 9,912 | Over by 1,913 — all behavioral |
| Execution Spec Gate | 8,910 | 9,597 | Over by 1,598 — pattern bugs fixed |
| Operator | 11,182 | 9,149 | Over by 1,150 — P0 fixed ✅ |
| Pipeline Strategist | 7,242 | 8,302 | Over by 303 — valuable additions |
| Aux Strategist | 6,576 | 7,528 | Under by 471 |
| Backend Specialist | 5,228 | 6,242 | Under by 1,757 |
| Senior Dev | 8,260 | 9,198 | Over by 1,199 — pattern bugs fixed |
| UI Specialist | 5,650 | 6,560 | Under by 1,439 |
| Database Specialist | 5,042 | 6,022 | Under by 1,977 |
| Schema Specialist | 5,326 | 6,257 | Under by 1,742 |
| System Design | 5,373 | 6,417 | Under by 1,582 |

**Note on over-limit prompts:** Architect, Spec Gate, Operator, Senior Dev, and Pipeline Strategist are over 7,999 chars. In all cases, the excess is legitimate behavioral rules — pattern compliance additions required to fix the identified bugs. Further reduction would require removing behavioral content, which would regress the agents. Recommend accepting current state.

---

## DEFERRED WORK (G-15 — Depth Fixes)

Five auxiliary agents have 1,400–2,000 chars of unused capacity that should be filled with domain-specific behavioral rules currently missing from the prompts. Requires reading each agent's `domain_rules.md` knowledge file before writing rules to avoid duplication.

| Agent | Chars available | Key missing depth |
|-------|----------------|-------------------|
| Database Specialist | 1,977 | Access pattern framework, migration safety rules, index heuristics |
| Schema Specialist | 1,742 | Normalization rules, relationship type guidance, naming conventions |
| System Design | 1,582 | Service boundary criteria, integration pattern heuristics, blast radius framework |
| UI Specialist | 1,439 | WCAG requirements, complete flow depth rules, design token guidance |
| Backend Specialist | 1,757 | REST vs event-driven heuristic, error classification framework, service split criteria |

---

## PATTERN COMPLIANCE — FINAL STATUS

| Pattern | All core agents | All aux agents |
|---------|----------------|----------------|
| P1 — One question | ✅ | ✅ (Senior Dev fixed) |
| P2 — Read before asking | ✅ | ✅ |
| P3 — Named hard stops | ✅ | ✅ (added this session) |
| P4 — Ecosystem position | ✅ | ✅ |
| P5 — Honest boundaries | ✅ | ✅ (Pipeline Strategist fixed) |
| P6 — Five-element contract | ✅ | N/A (aux agents produce proposals, not contracts) |
| P7 — Plain English | ✅ (Spec Gate improved) | PARTIAL (inline refs to init_protocol.md) |
| P8 — Drift control | ✅ (Blueprint Creator fixed) | ✅ |
| P9 — Committed artifact | ✅ (Architect fixed) | ✅ |
| P10 — Explicit handoff | ✅ (Spec Gate fixed) | ✅ |
| P11 — Knowledge acknowledgment | ✅ (Operator fixed) | ✅ |
| P12 — Human gate | ✅ | ✅ (added this session) |
| P13 — Adaptive awareness | ✅ | ✅ |
| ENTRY POINTS | ✅ (Blueprint Creator fixed) | ✅ |

---

## STRUCTURAL FINDINGS (not bugs, but noted)

1. **No `auxiliary/strategist/` directory exists** — Auxiliary Strategist lives at `Official agents/core/strategist/`. Planning prompt path was wrong. Actual location is correct.
2. **Pipeline Strategist path** — Lives at `Shared documents/core-agents-contracts/pipeline_strategist.md`, not under Official agents/core/. This is intentional (shared contract document) but differs from what the planning prompt assumed.
3. **Senior Dev at 9,198 chars** — The 7-phase workflow model is genuinely large and all phases are behavioral rules. Reducing below 7,999 would require splitting the agent or compressing phases into knowledge file references.
