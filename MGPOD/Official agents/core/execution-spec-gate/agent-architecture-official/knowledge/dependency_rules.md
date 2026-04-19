# Dependency rules (`depends_on`)

## Model

- Tasks form a **DAG**: directed edges `task → depends_on[]` (this task waits on listed ids).
- **Cycle** = invalid output → fix or BLOCK.

## Allowed edges

- `depends_on` MAY reference only `id` values of other objects in the **same** JSON array.
- **No** self-dependency.
- **Transitive closure** must not imply cycles.

## Ordering logic

- Array order = suggested execution order for humans; **eligibility** = all `depends_on` tasks logically complete before start.
- If task B needs artifact from task A, set B’s `depends_on` to include A’s `id`.
- **Infrastructure / schema / migration** tasks that REQ text implies must exist before feature code → depend on those infra tasks explicitly.

## Inference limits

- If Section B does not state a dependency but task B **cannot** start without A’s output → encode `depends_on`. If whether B needs A is **unclear** → **ASK** or **BLOCK** (never guess).

## Empty dependencies

Use `depends_on: []` when no prior task in this batch is required.
