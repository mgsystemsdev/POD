# Task spec (`tasks.json` element)

Output of Execution Spec Gate, not Architect. Architect **designs** contracts so Gate can fill this shape without clarification.

## Object schema (final)

| Field | Type | Required | Definition |
|-------|------|----------|--------------|
| `id` | string | yes | Stable unique task id (Gate convention). |
| `title` | string | yes | `<Scope> / <Sub-scope>: <Action>` |
| `description` | string | yes | **Execution prompt** — self-sufficient per [translation_rules.md](translation_rules.md). |
| `success_criteria` | string | yes | Observable pass condition from REQ **Done when** + Output. |
| `failure_behavior` | string | yes | From REQ **Failure path**; concrete. |
| `requirement_ref` | string | yes | Single REQ-ID (e.g. `REQ-004`). **One task → one REQ.** |
| `tier` | integer | yes | `1`, `2`, or `3` only. |
| `depends_on` | array of string | yes | Task ids; empty array if none. |

## Field rules

- **`description`:** Primary input to execution tools; must not require PRD lookup.
- **`success_criteria`:** Objective proof modality inferable (test, command, log, HTTP, artifact).
- **`requirement_ref`:** Immutable for a scope unless PRD versioned; renaming orphans traceability.

## Description template

See [translation_rules.md](translation_rules.md#description-template-spec-gate-assembles-architect-must-supply-content).
