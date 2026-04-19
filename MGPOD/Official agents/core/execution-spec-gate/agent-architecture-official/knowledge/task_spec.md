# Task schema (strict)

## Output shape

Single JSON **array** of objects. Each object has **exactly these 8 keys** — no others, no nulls unless `depends_on` is empty array.

| Field | Type | Rules |
|-------|------|--------|
| `id` | string | `TASK-001`, `TASK-002`, … zero-padded to 3 digits; unique; sequential in output order |
| `title` | string | `[Scope] / [Sub-scope]: [action]`; action-led; matches task_generation title pattern |
| `description` | string | **Execution prompt**; MUST follow `description_template.md` (all six labeled blocks) |
| `success_criteria` | string | Observable, testable; derived from REQ **Output** + **Done when** only |
| `failure_behavior` | string | Derived from REQ **Failure path** only; concrete system behavior |
| `requirement_ref` | string | Single `REQ-###` present in Section B |
| `tier` | integer | `1`, `2`, or `3` only |
| `depends_on` | array | Strings of `id` values; only tasks in same array; **DAG** (no cycles); `[]` if none |

## Invalid task definitions (reject entire output)

- Missing or extra keys.
- `description` missing any template section or not self-sufficient without PRD.
- `success_criteria` subjective (“works”, “polished”) or untestable.
- `failure_behavior` empty, generic (“fail gracefully”), or not from Failure path.
- `requirement_ref` not exactly one REQ from input, or REQ missing from Section B.
- `depends_on` references unknown `id`, future `id`, or creates cycle.
- Duplicate `id` or duplicate task covering the same atomic unit without reason.

## Execution independence

Reader of **`description` alone** must implement and verify without opening Section A or PRD. If not possible → **BLOCK**, do not emit.
