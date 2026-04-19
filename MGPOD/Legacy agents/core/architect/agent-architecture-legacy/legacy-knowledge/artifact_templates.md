# artifact_templates.md
# The Architect — Agent-Specific Knowledge
# System Version: v1.0

---

## PURPOSE

This file contains the exact output format for every artifact The Architect produces. Follow these templates exactly. Downstream agents depend on consistent formatting. Deviating from the template breaks the pipeline.

The Architect produces one document with two sections. Both sections are produced together when questioning is complete. Never produce them separately.

---

## OUTPUT STRUCTURE

```
project.md
├── ===== SECTION A: FULL PRD =====
│   Complete project reference document
│   Miguel reads this. Commits it to Git. Uses it for PRD updates.
│
└── ===== SECTION B: HANDOFF SUMMARY =====
    Compact summary for downstream agents
    Miguel pastes this into: Execution Spec Gate, The Operator, The Strategist
```

Tell Miguel exactly this when producing the output:
"Here is your project.md. Section A is your full PRD — save this to [project-root]/.claude/project.md and commit it to Git. Section B is your handoff summary — paste this as the opening message whenever you open the Execution Spec Gate, The Operator, or The Strategist."

---

## SECTION A — FULL PRD TEMPLATE

```
# [Project Name] — PRD
# Version: 1.0
# Last Updated: [date]
# Status: [Draft / Active / Updated]

---

## 0. DOCUMENT CONTROL

Version history:
- 1.0 [date]: Initial PRD — [brief description of what was designed]

Change log (append on every update, never delete):
- [date]: [what changed and why]

---

## 1. SYSTEM IDENTITY

Name: [project name]
Type: [one sentence — what kind of system this is]
Problem: [one to two sentences — what breaks or is painful without this system]
Owner: Miguel González
Primary users: [who uses this system and what they need]

Success condition for v1:
[Specific, observable, testable statement of what done looks like for version one]

---

## 2. REQUIREMENTS

[One entry per requirement. All five elements. No exceptions.]

### REQ-001: [Requirement Name]

Trigger: [what starts this]
Input: [exact data, format, valid values, invalid values]
Output: [exact result, format, what success looks like]
Constraints: [time, volume, accuracy, dependencies]
Failure path: [retry logic, error state, fallback, notification]

Done when: [testable statement — what must be observable for this to be verified complete]

---

### REQ-002: [Requirement Name]

[Same structure]

---

[Continue for all requirements]

---

## 3. DATA MODEL

### [Entity Name]
Table: [table_name]
| Column | Type | Required | Notes |
|--------|------|----------|-------|
| id | INTEGER | yes | Primary key, auto-increment |
| [field] | [type] | [yes/no] | [constraint or note] |
| created_at | TEXT | yes | ISO timestamp |
| updated_at | TEXT | yes | ISO timestamp |

Valid status values: [list if status field exists]
Allowed transitions: [state machine if applicable]

Indexes:
- [index name] on [columns] — reason: [what query this supports]

### [Entity Name]
[Same structure]

Relationships:
- [Entity A] has many [Entity B] via [foreign key]
- [Entity B] belongs to one [Entity A]

---

## 4. CORE WORKFLOW

### Workflow: [Name]

Entry point: [what triggers this workflow]

Steps:
1. [action] → [result]
2. [action] → [result]
   - If [condition]: [path A]
   - If [condition]: [path B]
3. [action] → [result]

Exit condition: [what constitutes completion]

State transitions:
- [entity] moves from [status A] to [status B] when [condition]
- [entity] moves from [status B] to [status C] when [condition]

Edge cases:
- [edge case]: [how it is handled]
- [edge case]: [how it is handled]

---

## 5. ARCHITECTURE

System type: [monolith / service / pipeline / agent]

Layer structure:
- [Layer name]: [one sentence responsibility]
- [Layer name]: [one sentence responsibility]
- [Layer name]: [one sentence responsibility]

Key components:
- [Component]: [single responsibility in one sentence]
- [Component]: [single responsibility in one sentence]

Communication: [how components interact — direct calls, events, queues]

External dependencies:
- [Dependency]: [what it does] | Failure behavior: [what happens if it is unavailable]

Architectural constraints (hard rules — never violate):
- [constraint]
- [constraint]

Explicitly forbidden:
- [pattern or approach that must never appear in this codebase]

---

## 6. TECHNICAL SPECIFICATIONS

Business rules (invariants — always true regardless of input):
- [rule]: [what must always hold]
- [rule]: [what must always hold]

Validation:
- [field/input]: [valid values] | Invalid behavior: [what happens with invalid input]

Authentication: [none / describe if present]

Performance targets:
- [operation]: must complete within [time] for [volume] records

Error format:
```json
{
  "error": "[error_code]",
  "message": "[human readable]",
  "detail": "[optional additional context]"
}
```

Logging:
- [what is logged]: [where it is stored]

---

## 7. FILE STRUCTURE

```
[project-root]/
├── .claude/
│   ├── project.md
│   ├── tasks.json
│   ├── session.md
│   └── decisions.md
├── [main entry point]
├── [key directory]/
│   ├── [file]: [purpose]
│   └── [file]: [purpose]
└── [key directory]/
    ├── [file]: [purpose]
    └── [file]: [purpose]
```

---

## 8. API CONTRACTS

Base URL: [http://127.0.0.1:PORT]

| Method | Path | Description | Request body | Response |
|--------|------|-------------|--------------|----------|
| GET | /api/[resource] | [description] | none | [shape] |
| POST | /api/[resource] | [description] | [shape] | [shape] |

---

## 9. SUCCESS AND FAILURE CONDITIONS

### Version 1 is successful when:
- [observable condition]
- [observable condition]

### Version 1 has failed when:
- [observable condition]
- [observable condition]

### Known risks:
- [risk]: [likelihood] | Mitigation: [how it is addressed]

---

## 10. OPEN ASSUMPTIONS

[Things assumed to be true that have not been verified. These must be resolved before or during v1 build.]
- [assumption]: [what changes if this is wrong]

---

## 11. MVP SCOPE

### In v1:
- [feature/requirement]
- [feature/requirement]

### Deferred to v2:
- [feature]: [reason for deferral]
- [feature]: [reason for deferral]

### Explicitly out of scope (never in v1):
- [feature]: [reason]
```

---

## SECTION B — HANDOFF SUMMARY TEMPLATE

Section B is always produced immediately after Section A. It is derived from Section A — not a separate design exercise.

```
===== SECTION B: HANDOFF SUMMARY =====
# [Project Name] — Handoff Summary
# Derived from PRD v[version] — [date]

PROJECT: [name]
TYPE: [what kind of system — one sentence]

ARCHITECTURE:
[Two to three sentences: stack, layer structure, key pattern. Enough for any agent to understand the system without reading Section A.]

CRITICAL CONSTRAINTS:
- [hard rule #1]
- [hard rule #2]
- [hard rule #3]
- [add up to two more if needed]

MVP SCOPE:
- [what is in v1 — bullet per requirement or feature]

OUT OF SCOPE (v1):
- [what is explicitly not being built]

REQUIREMENTS:
REQ-001 [Name]: [trigger] → [output] | done when: [testable condition] | fails: [failure behavior in one sentence]
REQ-002 [Name]: [trigger] → [output] | done when: [testable condition] | fails: [failure behavior in one sentence]
[Continue for all requirements — one line each]

FILE STRUCTURE:
[project-root]/
├── [key file or directory]: [one word purpose]
├── [key file or directory]: [one word purpose]
└── [key file or directory]: [one word purpose]
[Keep to 8-10 lines maximum]

CURRENT STATE: [What exists and works right now. "Greenfield" if nothing exists yet.]
NEXT SCOPE: [The first scope of work — what gets built first]
===== END SECTION B =====
```

---

## PRODUCING THE OUTPUT — EXACT SEQUENCE

1. Complete all questioning. Run conflict detection.
2. Resolve all conflicts before producing any output.
3. Produce Section A in full.
4. Produce Section B immediately after Section A in the same message.
5. Tell Miguel:
   - Save this entire output as [project-root]/.claude/project.md
   - Commit to Git: git add .claude/project.md && git commit -m "docs: add project PRD v1.0"
   - Paste Section B as the opening message when opening: Execution Spec Gate, The Operator, or The Strategist
6. Provide the handoff message Miguel sends to the Execution Spec Gate:

"I have a new project ready for task generation. Here is the handoff summary: [paste Section B]"

---

## UPDATE MODE — MODIFIED OUTPUT

When The Architect runs in PRD UPDATE or SCOPE ADDITION mode, the output changes:

Section A: produce only the updated sections with a changelog entry added to section 0. Do not reproduce the entire PRD — produce the delta and the updated section clearly marked.

Section B: always reproduce Section B in full. Section B must always reflect the complete current state, not just the delta.

Tell Miguel:
- Replace the relevant sections in project.md with the updated content
- Append the changelog entry
- Commit: git add .claude/project.md && git commit -m "docs: update PRD — [what changed]"
- Section B is your new handoff summary — use this version going forward

---

## SCHEMA.JSON OUTPUT

When the project requires a structured JSON spec (complex data models, API-heavy systems), produce schema.json as a third artifact after Section B.

Schema.json is machine-readable. It is consumed by Claude Code and Cursor to understand the data model without reading prose.

Format: see schema.json knowledge file for the exact template.

Tell Miguel: save this as [project-root]/.claude/schema.json and commit alongside project.md.
