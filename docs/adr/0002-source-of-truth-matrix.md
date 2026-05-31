# ADR 0002: Source of truth matrix

**Status:** Accepted (Phase 0 — foundation)  
**Date:** 2026-05-15  
**Depends on:** [0001-system-ownership.md](./0001-system-ownership.md)

This document is the **authoritative reference** for who may **create**, **update**, and **read** each class of state in the new platform. If code or an ADR disagrees with this matrix, **this ADR must be updated first**.

**Legend**

| Column | Meaning |
|--------|---------|
| **Canonical owner** | The only writer for durable truth in the target environment (local vs cloud). |
| **Readers** | May read; must tolerate staleness unless they use version/ETag. |
| **Local projection** | Files or local DB rows **derived** from cloud or produced locally pending sync. |
| **Cloud projection** | API materialized views, cache, CDN—**not** authoritative alone. |
| **Sync direction** | Default data flow for MVP; arrows are not bidirectional unless stated. |

---

## A. Platform-wide resources

| Resource | Canonical owner (cloud) | Canonical owner (local) | Readers | Sync direction (MVP) | Notes |
|----------|-------------------------|---------------------------|---------|------------------------|--------|
| **Project / workspace** | Postgres (`projects`) | Daemon config + optional local `workspace.json` | Dashboard, daemon, workers | **Pull**: server → local metadata; **Push**: name/path hints only if server allows | Server assigns stable `project_id`. |
| **Identity / membership** | Postgres + IdP | Daemon stores **tokens only** (OS keychain preferred) | API, dashboard | Pull credentials; never push secrets to repo | No secrets in Postgres plaintext if avoidable. |
| **API keys / tokens** | KMS / secret store bound to API | Local secure store | Daemon, workers | Pull | Rotated server-side. |

---

## B. Documents (local-first editorial state)

Assume **one document key** for MVP (e.g. `governance/memory.md` mapped to `document_key = memory`).

| Resource | Canonical owner | Local projection | Readers | Sync direction (MVP) | Notes |
|----------|-----------------|----------------------------------|---------|------------------------|--------|
| **Document body (MVP type)** | **Postgres** (row + `content` + `version`) after server accepts write | **Working file** under workspace | Dashboard (via API), daemon | **Push**: file change → daemon → API **conditional write** (If-Match / version); **Pull**: API → file overwrite for cache refresh | Local edits are **proposals** until server ACK. |
| **Document version / ETag** | Postgres | Daemon manifest slot | All writers | Server is tie-breaker on conflict | Required for LWW safety. |
| **Wide-tree scan index** | Postgres (optional later) | Daemon-built manifest | Search UI | Push summaries | MVP may omit index. |

**Rule:** For collaborative documents, **Postgres content row is canonical after ACK**. The file is a **projection** for tools; “offline wins” requires an explicit **conflict branch** ADR later.

---

## C. Operational queue and execution

| Resource | Canonical owner | Local projection | Readers | Sync direction | Notes |
|----------|-----------------|----------------------------------|---------|----------------|--------|
| **Task (durable)** | Postgres | Optional cached listing for UI | Dashboard, orchestrator (read), workers | **Pull** listings; **Push** creates via API only | No `tasks.json` as SoT in new system unless legacy shim. |
| **Task status transitions** | Postgres (single writer: API or job completion path) | None authoritative | Dashboard, workers | Events only | Transitions go through application use cases + outbox. |
| **Execution job** | Postgres (`execution_jobs` or equivalent) | Worker in-memory lease | Worker, dashboard | Create via API; worker updates status | Worker does not invent jobs by scanning disk. |
| **Execution result / trace** | Postgres (+ optional object store for blobs) | Worker temp files until uploaded | Dashboard, audit | Worker → API **append** result | Large logs → blob pointer in row. |
| **Run / attempt** (per job) | Postgres | — | Dashboard | — | Immutable append for attempts preferred. |

---

## D. Orchestration (multi-step plans)

| Resource | Canonical owner | Local projection | Readers | Sync direction | Notes |
|----------|-----------------|----------------------------------|---------|----------------|--------|
| **Plan definition** | **Catalog** (versioned artifact) or Postgres `plan_templates` | Cached copy in workspace for air-gapped dev | Orchestrator | Pull catalog at deploy; optional push **templates** as products | Not the same as “a run.” |
| **Plan run state** | Postgres (`plan_runs`, `plan_steps`) | Optional export JSON for debugging | Orchestrator, dashboard | Worker/orchestrator writes via API | **No** sole reliance on `runs/<uuid>/` on disk in cloud era. |
| **Step artifacts (large)** | Object store (recommended) or Postgres blob | Local temp during step | Orchestrator | Upload after step | Small MVP may use Postgres only with size cap. |

---

## E. Governance and human-in-the-loop

| Resource | Canonical owner | Local projection | Readers | Sync direction | Notes |
|----------|-----------------|----------------------------------|---------|----------------|--------|
| **Proposed action** | Postgres | — | Dashboard | API | Approve/reject transitions + outbox. |
| **Approval audit row** | Postgres | — | Compliance, dashboard | API | Append-only. |
| **Policy / feature flag** | Postgres (or config service) | Daemon cached snapshot | All | Pull periodic | Not per-task files. |

---

## F. Events and integration

| Resource | Canonical owner | Local projection | Readers | Sync direction | Notes |
|----------|-----------------|----------------------------------|---------|----------------|--------|
| **Outbox / event log** | Postgres (`outbox` table) | — | Dispatchers, projectors, webhooks | Append in same txn as domain row | **Source of truth for “what happened.”** |
| **Webhook delivery cursor** | Postgres | — | Dispatcher | — | At-least-once delivery; consumers idempotent. |
| **Analytics / BI** | Warehouse (future) | — | — | ETL from outbox/projectors | Not MVP. |

---

## G. Agent and content catalog

| Resource | Canonical owner | Local projection | Readers | Sync direction | Notes |
|----------|-----------------|----------------------------------|---------|----------------|--------|
| **Catalog release (MGPOD-like)** | Git tag / artifact registry / packaged bundle | Clone or cache on machine | Orchestrator, validators | Pull at deploy or daemon “catalog update” | **Read-heavy**; not mutated by normal task execution. |
| **Resolved “agent bundle” for a run** | Immutable snapshot ref (hash) stored on **job** or **plan run** | — | Execution, audit | Pin at enqueue time | Reproducibility and audits. |

---

## H. Dashboard and clients

| Resource | Canonical owner | Readers | Notes |
|----------|-----------------|---------|--------|
| **UI ephemeral state** | Browser only | User | Filters, scroll, selection—not synced unless product requires. |
| **Cached API responses** | Browser / CDN | User | Must respect ETag / TTL; never written back as SoT. |

---

## I. Explicit non–source-of-truth (legacy / forbidden as canonical)

| Artifact | Role in new platform |
|----------|------------------------|
| **`~/.claude/tasks.json` as queue** | **Forbidden** as canonical queue; max **legacy import** source with one-way migration. |
| **SQLite peer to Postgres** | **Forbidden** for new cloud SoT; optional **daemon-only** embedded cache per ADR open decision. |
| **Orchestrator silent append to task files** | **Forbidden** (see ADR 0001 §4). |

---

## J. Write path checklist (for PRs)

Before merging code that **mutates** state, confirm:

1. **Which cell** in this matrix is the canonical owner for that mutation?
2. **Is an outbox event** emitted in the **same transaction**?
3. **Are readers** listed here updated via **pull**, **push**, or **event projection** only?
4. **Does any path** violate ADR 0001 §4? If yes, stop and split the change.

---

## K. MVP slice mapping (cross-reference ADR 0001 §6)

| Capability | Matrix rows involved |
|------------|----------------------|
| One project | §A |
| One document type | §B |
| One task / job type | §C |
| File → cloud | §B push path + §F outbox `DocumentPatched` |
| Dashboard reflects | §B readers via API; §H cache rules |
| One execution job | §C jobs + results + §F events |
| Traceability | §F outbox for all transitions |

---

## Consequences

- Code generators, daemons, and workers **must** import stable names from this matrix (e.g. `DocumentRepository`, `OutboxWriter`) that **do not** embed SoT policy as stringly-typed paths.
- Any new resource type requires a **PR that updates this ADR** with a new row before merge.

## References

- [0001-system-ownership.md](./0001-system-ownership.md) — system purpose, runtimes, bans, MVP slice, open decisions.
- [0003-repository-structure.md](./0003-repository-structure.md) — where code enforcing this matrix should live.
- [0004-event-model.md](./0004-event-model.md) — events, outbox, and projections tied to SoT writers.
- [0005-synchronization-protocol.md](./0005-synchronization-protocol.md) — sync protocol and manifest (implements SoT for documents).
