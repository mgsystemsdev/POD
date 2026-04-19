# Infrastructure-first ordering

## Detection (when to emit infra tasks)

Emit **Infrastructure** scope tasks **before** feature tasks when Section B (including Architecture, File Structure, Current State, Requirements) implies any of:

- New persistence (tables, columns, indexes), migrations, or schema sync not already in Current State
- New runtime services, workers, or pipelines required before feature code can run
- Net-new API surfaces that other tasks assume exist

If “migration vs greenfield” is **unclear** from Section B → **BLOCK** or **ASK**; do not assume schema.

## Ordering

1. **Infrastructure** tasks first in the array (still respect `depends_on` among infra tasks).
2. **Feature** tasks after infra they depend on.
3. Same `requirement_ref` MAY appear on infra tasks when REQ explicitly owns setup; otherwise infra maps to the REQ that implies the persistence/capability — if mapping is ambiguous → **BLOCK**.

## Schema dependency logic

- Data-dependent feature tasks MUST `depends_on` the task that applies the schema/migration they need.
- Do not order a feature task before the migration task that introduces its tables/fields.

## Naming

Use scope **Infrastructure** in `title` prefix: `Infrastructure / [Sub-scope]: ...`

## No invention

DDL, migration filenames, or tool commands not implied by Section B → **BLOCK** (Architect must specify intent).
