# Translation rules

## Core rule

**`description` = execution prompt.** Self-sufficient: plan + implement + verify **without** re-opening the PRD.

Architect makes Requirements, Critical Constraints, and Architecture literal enough that Spec Gate can pack **`description`** without inventing facts.

## Requirement → task mapping

| REQ source | `tasks.json` field |
|------------|-------------------|
| Output + Done when | `success_criteria` |
| Failure path | `failure_behavior` |
| Trigger + Input + Constraints | `description` (context, rules, validations) |
| REQ identity | `requirement_ref` (e.g. `REQ-003`) |
| Scope | `title`: `<Scope> / <Sub-scope>: <Action>` |
| Ordering | `depends_on` (from Section A deps) |

**Traceability:** exactly **one** `requirement_ref` per task. No task without REQ-ID.

## Mapping rules

1. Every MVP deliverable path appears as REQ with 5/5 + Done when.
2. Persistence changes: entities, fields, migrations stated in Section A **before** feature REQs that need them (**infrastructure-first**).
3. No “extra” work in tasks without matching REQ in Section A/B.

## Description template (Spec Gate assembles; Architect must supply content)

Plain text; all blocks present in substance:

```
OBJECTIVE: [1–3 sentences]

REQUIREMENT: [requirement_ref]: [full contract restatement]

ARCHITECTURAL CONSTRAINTS:
- [from Critical Constraints / Architecture]

DONE WHEN: [Done when line]

FAILURE BEHAVIOR: [Failure path]

DO NOT:
- [forbidden actions]
```

## Gate failures Architect prevents

| Gate failure | Prevention |
|--------------|------------|
| Missing contract element | No incomplete 5/5 |
| Unmeasurable `success_criteria` | Observable Output + Done when |
| Missing `failure_behavior` | Concrete Failure path |
| Ambiguous architecture | Architecture + Critical Constraints explicit |
| Task without REQ | No orphan tasks |
| Wrong order | Infra/schema/migrations in Section A before dependent features |

## Schema reference

See [task_spec.md](task_spec.md) for object shape. Keys: `id`, `title`, `description`, `success_criteria`, `failure_behavior`, `requirement_ref`, `tier`, `depends_on`. No extra keys unless importer doc requires.
