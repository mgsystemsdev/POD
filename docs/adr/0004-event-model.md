# ADR 0004: Event model for the AI operations platform

**Status:** Proposed  
**Date:** 2026-05-15  
**Depends on:** [0001-system-ownership.md](./0001-system-ownership.md), [0002-source-of-truth-matrix.md](./0002-source-of-truth-matrix.md), [0003-repository-structure.md](./0003-repository-structure.md)

This ADR defines the **event philosophy**, **taxonomy**, **canonical schema**, **outbox architecture**, **projections**, **orchestration and sync event families**, **failure handling**, and **anti-patterns** for the event-driven, local-first platform.

---

## 1. Event philosophy

| Principle | Definition |
|-----------|------------|
| **Immutable append-only** | Published events are **never updated or deleted** in the primary log. Corrections are **new events** (e.g. `DocumentCorrected`, `TaskStatusRevertedByAdmin`). Aggregates may move forward; the log stays append-only. |
| **Causality** | Every event carries **`causation_id`** = the `event_id` of the command or event that directly caused it (chain root = self or null). Enables distributed tracing of “why this happened.” |
| **Replayability** | Given the same ordered event stream (per partition) and deterministic projector code, **read models can be rebuilt**. Payloads must be **self-contained** or reference **versioned snapshots** (e.g. `content_hash`, `blob_uri`)—not “whatever is on disk now.” |
| **Auditability** | Events are the **legal record** of intent and effect: **who** (`actor`), **when** (`occurred_at` / `recorded_at`), **what** (`event_type`, `payload`), **on which aggregate** (`aggregate_type`, `aggregate_id`). |
| **Idempotency** | **Consumers** and **dispatchers** must tolerate duplicates. **`idempotency_key`** (optional) or **`event_id`** uniqueness prevents double application of the same published fact. |

**Non-goals:** Events are not a chat transcript; **command** documents may exist internally but **facts** published to the log are events.

---

## 2. Core event categories (taxonomy)

Events are grouped by **category** (namespace prefix). `event_type` is `category.action` in lowercase snake_case.

| Category | Prefix | Examples (non-exhaustive) |
|----------|--------|---------------------------|
| **Document** | `document.` | `document.created`, `document.updated`, `document.deleted`, `document.version_bumped` |
| **Sync** | `sync.` | `sync.file_detected`, `sync.started`, `sync.conflict_detected`, `sync.committed`, `sync.failed` |
| **Task** | `task.` | `task.created`, `task.assigned`, `task.status_changed`, `task.cancel_requested`, `task.archived` |
| **Execution** | `execution.` | `execution.job_enqueued`, `execution.job_started`, `execution.job_completed`, `execution.job_failed`, `execution.artifact_stored` |
| **Orchestration** | `orchestration.` | See §7 |
| **Approval / governance** | `governance.` | `governance.proposal_created`, `governance.proposal_approved`, `governance.proposal_rejected`, `governance.policy_violation_recorded` |
| **System** | `system.` | `system.outbox_dispatch_started`, `system.projector_lag_breached`, `system.schema_migrated` |

**Taxonomy rule:** New `event_type` values are **registered** in `packages/contracts` (JSON Schema per type) before production emitters ship.

---

## 3. Canonical event schema

Every stored event conforms to an **envelope** (metadata) + **typed payload** (validated JSON).

### 3.1 Envelope (required fields)

| Field | Type | Description |
|-------|------|-------------|
| **`event_id`** | ULID or UUIDv7 | Globally unique, **time-sortable** preferred (ULID) for index-friendly ordering. |
| **`event_type`** | string | `category.action` from taxonomy. |
| **`schema_version`** | int | Envelope schema version (start at `1`). |
| **`occurred_at`** | RFC3339 UTC | When the fact happened **in domain time** (client or server clock). |
| **`recorded_at`** | RFC3339 UTC | When the row was **committed** to the outbox / event store (server). |
| **`aggregate_type`** | string | e.g. `project`, `document`, `task`, `execution_job`, `plan_run`. |
| **`aggregate_id`** | string | Stable id (often UUID string); composite aggregates use deterministic encoding. |
| **`aggregate_version`** | int | Monotonic **per aggregate** optimistic concurrency; incremented on each state-changing event for that aggregate. |
| **`causation_id`** | string \| null | `event_id` of direct cause. |
| **`correlation_id`** | string | Spans sync → API → worker → orchestrator for one operator intent. |
| **`actor`** | object | `{ "type": "user" \| "system" \| "daemon" \| "worker" \| "orchestrator", "id": "...", "claims": { ... } }` — no PII in free text. |
| **`idempotency_key`** | string \| null | Stable key for **command deduplication** at API boundary (optional). |
| **`payload`** | object | Type-specific; validated against `contracts/events/<event_type>.schema.json`. |

### 3.2 Storage layout

- **`events`** (or **`domain_events`**) table: envelope columns + `payload JSONB` + indexes on `(aggregate_type, aggregate_id, aggregate_version)`, `(recorded_at)`, `(correlation_id)`, `(event_type)`.
- **`outbox`** table: same `event_id` (FK or duplicate), `dispatch_status`, `available_at`, `attempts`, `last_error` — see §5.

**Ordering guarantee (per aggregate):** `(aggregate_type, aggregate_id, aggregate_version)` is **strictly increasing**; consumers processing aggregate streams must process in `aggregate_version` order.

**Example (JSON document):**

```json
{
  "event_id": "01JABC1234567890ABCDEFGH",
  "event_type": "document.updated",
  "schema_version": 1,
  "occurred_at": "2026-05-15T12:00:01Z",
  "recorded_at": "2026-05-15T12:00:01.042Z",
  "aggregate_type": "document",
  "aggregate_id": "proj:01H…/doc:memory",
  "aggregate_version": 14,
  "causation_id": "01JABC0987654321ZYXWVUTS",
  "correlation_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "actor": { "type": "daemon", "id": "sync-daemon@host-abc", "claims": {} },
  "idempotency_key": "sync:sha256:…:v13",
  "payload": {
    "document_key": "memory",
    "content_hash": "sha256:…",
    "byte_size": 1204,
    "client_patch_id": "01J…"
  }
}
```

---

## 4. Event ownership

| Role | May emit | May consume | May mutate aggregate rows |
|------|----------|-------------|---------------------------|
| **Cloud API (use cases)** | All domain-changing events **via outbox in same txn** as aggregate write | N/A (producer) | **Only** through repositories inside `UnitOfWork` |
| **Sync daemon** | `sync.*`, and **commands** that become **`document.*`** only after API accepts (daemon emits `sync.*`; API emits `document.*` on success) — **either** pattern is valid if ADR picks one: (A) daemon posts commands, API emits facts; (B) daemon emits `sync.committed` only after API returns 200 and API wrote `document.updated`. **Recommended:** API is sole emitter of `document.*`; daemon emits `sync.*` pre/post. | API responses, conflict payloads | **Never** Postgres directly |
| **Execution worker** | `execution.*` | Lease table / job API | Job + run rows **only** through API or shared `application` use cases invoked with service credentials |
| **Orchestrator** | `orchestration.*`, may enqueue `execution.*` via API | `orchestration` state, catalog pins | Plan aggregates via API or shared libs—not dashboard |
| **Dashboard** | **None directly** — sends **commands** (HTTP) that result in API-emitted events | Read models / SSE feed | **None** |
| **Projectors** | `system.projector_*` (optional) | `events` / `outbox` | **Read model** tables only |
| **Outbox dispatcher** | Dispatch side-effects (webhooks); may append `system.*` | `outbox` | **Not** domain aggregates |

**Golden rule:** **Exactly one writer** to each aggregate’s canonical row per transaction—the **use case**—and it appends **1..N events** atomically with that write.

---

## 5. Outbox architecture

### 5.1 Transactional outbox pattern

Within a single DB transaction:

1. Mutate aggregate row(s) + bump `aggregate_version`.
2. Insert row(s) into **`events`** (immutable) **or** insert into **`outbox`** pointing to `event_id` (if split table).
3. Commit.

**Dispatcher** (separate process or loop): reads `outbox WHERE dispatch_status = 'pending' AND available_at <= now()` **FOR UPDATE SKIP LOCKED**, delivers to consumers, marks **`delivered`** or schedules retry.

### 5.2 Dispatching

- **At-least-once** delivery to external systems is assumed.
- **Internal projectors** should use the same `events` table or a **changefeed** (logical decoding) in later scale-out; MVP: dispatcher invokes in-process projector registry.

### 5.3 Retries

- Exponential backoff with jitter; cap `max_attempts`.
- **Transient errors** (5xx, timeout): retry.
- **Permanent errors** (4xx schema mismatch on webhook): move to **DLQ** after N attempts.

### 5.4 Dead-letter handling

- Table **`outbox_dead_letter`** (or status `dead`) with `event_id`, `last_error`, `attempts`, `failed_at`.
- Operator tooling: **replay** by cloning row to new `outbox` entry with new `dispatch_id` or manual **re-publish** after fix.

### 5.5 Idempotency strategy

| Layer | Mechanism |
|-------|-----------|
| **API** | `Idempotency-Key` header → unique partial index on `(tenant_id, idempotency_key)` for command acceptance. |
| **Outbox dispatch** | Unique `event_id`; webhook consumers return dedupe token. |
| **Projectors** | Store `last_processed_event_id` or `last_aggregate_version` per projection shard; updates must be **idempotent** (upsert by natural key). |

---

## 6. Projections / read models

Projectors **subscribe** to `events` (or outbox fan-out) and maintain **query-optimized** tables or materialized views.

| Projection | Source events | Purpose |
|------------|---------------|---------|
| **Dashboard document list** | `document.*`, `sync.*` (for badges) | Fast listing with `title`, `key`, `version`, `updated_at`, `sync_state`. |
| **Task board** | `task.*`, `execution.*` | Columns: status, assignee, last_run_id, error summary. |
| **Sync status** | `sync.*` | Per path: `last_commit_at`, `last_error`, `conflict_flag`. |
| **Execution trace** | `execution.*` | Timeline for a `task_id` / `job_id`: started, tokens (if allowed), completed/failed. |
| **Analytics** | All categories | Rollups to warehouse via batch ETL; not on hot path. |

**CQRS boundary:** Commands **never** read projections for authority—only for UX hints; **authority** remains aggregates + events.

---

## 7. Orchestration events (required set)

| `event_type` | When emitted | Typical payload keys |
|--------------|--------------|----------------------|
| **`orchestration.plan_started`** | Plan run accepted | `plan_id`, `plan_version`, `plan_run_id`, `input_summary_ref` |
| **`orchestration.step_started`** | Step lease acquired | `plan_run_id`, `step_id`, `agent_bundle_ref` |
| **`orchestration.step_completed`** | Step output validated | `plan_run_id`, `step_id`, `output_artifact_uri`, `token_usage` (optional) |
| **`orchestration.step_failed`** | Step failed after retries | `plan_run_id`, `step_id`, `error_code`, `retry_count`, `non_retryable` |
| **`orchestration.handoff_requested`** | Human required | `plan_run_id`, `step_id`, `instructions_uri`, `expires_at` |
| **`orchestration.plan_completed`** | Terminal success | `plan_run_id`, `summary_ref` |
| **`orchestration.plan_failed`** | Terminal failure / abort | `plan_run_id`, `reason`, `failed_step_id` |

Orchestrator **does not** skip emitting `step_failed` before `plan_failed` when policy requires an audit chain.

---

## 8. Sync events (required set)

| `event_type` | When emitted | Notes |
|--------------|--------------|--------|
| **`sync.file_detected`** | Daemon observed change (post-debounce) | Payload: `path`, `content_hash`, `watcher_batch_id` |
| **`sync.started`** | Upload / compare began | Links to `correlation_id` |
| **`sync.conflict_detected`** | Server version ≠ client basis | Payload: `server_version`, `client_version`, `resolution_policy` |
| **`sync.committed`** | Server accepted new version | Precedes or pairs with `document.updated` per chosen split (§4) |
| **`sync.failed`** | Network / auth / validation | `retry_scheduled_at` optional |

**Local-first:** `sync.*` events may originate from daemon **after** local facts; **`document.*`** still require server authority for collaborative SoT ([0002](./0002-source-of-truth-matrix.md) §B).

Normative protocol (lifecycle, manifest, conflicts, API sketch): [0005-synchronization-protocol.md](./0005-synchronization-protocol.md).

---

## 9. Failure handling

| Concern | Policy |
|---------|--------|
| **Retries** | Outbox dispatcher exponential backoff; **orchestration step** retries per plan policy (distinct from outbox). |
| **Poison events** | After `max_attempts`, DLQ + alert; **no infinite spin**. |
| **Replay** | Rebuild projections from `events` ordered by `(recorded_at, event_id)` global **or** per-aggregate by `aggregate_version`. Global total order not required except where explicitly needed. |
| **Recovery** | `system.reprojection_started` / completed; operators re-run projector from checkpoint. |
| **Ordering guarantees** | **Per aggregate:** strict `aggregate_version` order. **Global:** `recorded_at` + tie-breaker `event_id` for audit timelines only—not for cross-aggregate invariants unless explicitly designed. |

---

## 10. Anti-patterns (merge-blocking)

| Ban | Rationale |
|-----|-----------|
| **Mutable events** | Breaks audit and replay; emit compensating events instead. |
| **Direct side effects without events** | Hidden state change; breaks projections and compliance. |
| **Hidden writes** | Any aggregate write without outbox row in same txn. |
| **Polling-based synchronization replacing events** | Cron full diff as **sole** truth mechanism—allowed only as **reconciliation**, not replacement for event log; dashboard refresh polling is **UX only**, not SoT sync. |

---

## Output summary (quick reference)

### Event taxonomy

- Namespaced `event_type`: `document.*`, `sync.*`, `task.*`, `execution.*`, `orchestration.*`, `governance.*`, `system.*`.

### Schemas

- Envelope §3.1 + `packages/contracts/events/*.schema.json` per `event_type`.

### Event lifecycle

```mermaid
sequenceDiagram
  participant Client as Client / Daemon
  participant API as API use case
  participant DB as Postgres
  participant OB as Outbox dispatcher
  participant PR as Projectors

  Client->>API: Command + Idempotency-Key
  API->>DB: BEGIN; update aggregate; insert events+outbox; COMMIT
  OB->>DB: claim outbox rows
  OB->>PR: deliver / invoke
  PR->>DB: update read models (idempotent)
  OB->>DB: mark delivered / DLQ
```

### Projection architecture

- **Write path:** aggregates + events + outbox (txn).  
- **Read path:** projectors → tables/views → API list endpoints.  
- **Dashboard:** HTTP/SSE against read APIs only.

### Outbox flow

- **Write:** same transaction as domain change.  
- **Read:** dispatcher `SKIP LOCKED`, retries, DLQ.  
- **Consumers:** idempotent; external webhooks at-least-once.

### Replay strategy

- **Cold replay:** truncate projection table → replay `events` from offset.  
- **Dual-write migration:** old + new projectors until checksum match; then cut.

### Operational guarantees

- **Per-aggregate ordering** and **optimistic concurrency** via `aggregate_version`.  
- **At-least-once** dispatch; **exactly-once effects** only where consumers dedupe.  
- **Audit:** immutable `events` + `recorded_at` + `actor`.

---

## References

- [0001-system-ownership.md](./0001-system-ownership.md) — outbox requirement §5.
- [0002-source-of-truth-matrix.md](./0002-source-of-truth-matrix.md) — writers vs projections.
- [0003-repository-structure.md](./0003-repository-structure.md) — packages for contracts and projectors.
- [0005-synchronization-protocol.md](./0005-synchronization-protocol.md) — sync lifecycle and reconciliation tied to `sync.*` / `document.*`.
