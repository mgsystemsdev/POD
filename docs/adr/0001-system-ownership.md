# ADR 0001: System ownership and architecture contract

**Status:** Accepted (Phase 0 — architecture contract)  
**Date:** 2026-05-15  
**Context:** Greenfield / rewrite alignment for the AI operations platform.  
**Supersedes:** Informal assumptions scattered across legacy docs and scripts.

---

## 1. System purpose

This platform is **not** a chatbot, a single-purpose agent wrapper, or a demo “ask the model” app.

It is a **local-first AI operations platform** with a **cloud control plane**:

- **Local-first:** Operators and AI tooling work against a **project workspace on disk** (or an explicit local cache) as the primary place to edit, run tools, and iterate quickly—often offline or behind strict egress.
- **Cloud control plane:** A **hosted API and dashboard** provide durable coordination, visibility, approvals, multi-device access, and operational policy—backed by **Postgres** as the system of record for collaborative and automated state.
- **Operations:** The product optimizes for **queues, runs, sync, governance, and traceability**—not for ephemeral conversation transcripts as the center of gravity.

Companion matrix: [0002-source-of-truth-matrix.md](./0002-source-of-truth-matrix.md).  
Repository layout and dependency rules: [0003-repository-structure.md](./0003-repository-structure.md).

---

## 2. Core runtimes

These are **separate deployable or runnable systems** with **narrow contracts**. They must not collapse into one “god process.”

| Runtime | Role |
|--------|------|
| **Local sync daemon** | Watches configured roots, debounces changes, computes patches, **pushes** and **pulls** document and manifest state vs the cloud API. **No AI execution.** |
| **Cloud API / backend** | Authenticated HTTP (and later RPC) surface: commands, queries, webhooks, idempotent ingest. **Owns validation, authorization, and persistence orchestration** (including outbox writes in the same transaction as domain mutations). |
| **Postgres database** | Durable storage for projects, tasks, runs, orchestration state, governance, **transactional outbox**, and projections. **Not** a file server. |
| **Execution worker** | Consumes **execution jobs** from a queue or job table; calls the **AI execution engine** (LLM / tools / subprocess per job type). **Does not** scan arbitrary project trees for sync. |
| **Orchestrator service** | Drives **multi-step plans** (DAG, handoffs, retries, compensations where defined). Emits domain events; persists plan state via the API or shared libraries—**does not** replace the sync daemon or the execution worker’s job queue. |
| **Dashboard** | UI for humans: browse state, approve actions, trigger runs, resolve conflicts. **Client** of the cloud API only. |
| **Agent / content catalog** | Versioned definitions (prompts, skills, contracts)—**read-heavy** artifact set used to **configure** runs and validation. **Not** the live runtime database for task queues. |

---

## 3. Source of truth rules

High-level rule: **every resource has exactly one canonical owner** for mutation; everything else is a **projection**, **cache**, or **derived view**. Details live in [0002-source-of-truth-matrix.md](./0002-source-of-truth-matrix.md).

| Surface | Owns (may mutate canonical state) | Does not own |
|--------|-----------------------------------|--------------|
| **Local repo / docs** | Working copy of files under the **declared workspace root**; ephemeral scratch; local-only config that is **not** authoritative for collaboration. | Durable multi-user truth for shared tasks without server acknowledgment. |
| **Postgres** | Canonical rows for **shared** operational entities: projects, tasks, runs, approvals, plan runs (when persisted), outbox, sync checkpoints, etc. | Raw skill markdown as the only copy (catalog should be versioned and addressable). |
| **Dashboard** | UI state only (filters, selection). All durable changes go **through the API**. | Source files on disk; direct DB connections in the browser. |
| **Sync daemon** | Local **manifest**, **cursor positions** (optional), **unsynced queue**, and **integrity hashes** for files it watches. | Business invariants for tasks/runs (server validates). |
| **Execution worker** | **Job lease**, partial **trace buffers**, and **worker-local temp** for the duration of a job. | Project-wide “walk and infer” ownership of documents. |
| **Orchestrator** | **Plan state machine** for plans it owns (when stored server-side); step completion markers; saga correlation IDs. | Silent writes to `tasks.json` or arbitrary `.claude/` paths as a side channel. |
| **Event / outbox log** | **Immutable append** of “what happened” for integration, audit, and projections. **Not** a substitute for the primary entity tables—it is the **journal** that keeps them honest. |

---

## 4. What must never happen

These are **hard bans** for reviews and automation:

1. **Dashboard directly owns source files** — No UI writing to `~/`, repo roots, or `.claude/` without going through the **sync daemon contract** or an explicit, audited **export** command.
2. **Agents directly mutate random files** — Model outputs produce **proposals** or **structured patches**; application code applies them with validation, paths confined to workspace policy, and events recorded.
3. **Execution worker scans project folders** — Workers consume **bounded job payloads** (paths, hashes, URIs). Discovery belongs to **sync** or **indexing** services—not the execution hot path.
4. **Sync daemon runs AI jobs** — Sync is **I/O + diff + network**; any “AI summary of the tree” is a separate **job** submitted to the execution engine.
5. **Orchestrator writes directly to task files** — No appending to global or project `tasks.json` as a hidden side effect; task creation flows through **API + outbox** (or explicitly deprecated legacy paths during strangler migration only).
6. **Business logic depends on local paths** — Domain and application layers use **ids, URIs, and workspace-scoped handles**. `Path.home()` / machine-specific layout exist only in **infrastructure adapters** behind a `RuntimePaths` or config port.

---

## 5. Event model

All **important state changes** (create/update/delete/status transitions, approvals, sync commits, execution completion/failure) **must** be recorded as **domain events** written through a **transactional outbox** in the same database transaction as the canonical row update.

- **Why:** Ordering, retries, multiple consumers (dashboard feed, analytics, email, billing), and forensic replay without scraping logs.
- **Consumers:** Projectors (read models), webhooks, internal workers—**after** commit, never inside the same transaction as external HTTP unless using a staged outbox publish pattern.
- **Correlation:** Every event carries `correlation_id` and `causation_id` where applicable for traces across sync → API → worker → orchestrator.

Full taxonomy, schema, outbox, projections, and failure policies: [0004-event-model.md](./0004-event-model.md).  
Local↔cloud sync protocol (manifest, conflicts, API contract): [0005-synchronization-protocol.md](./0005-synchronization-protocol.md).

---

## 6. Initial MVP slice

The first vertical build **proves** the architecture before breadth:

| Dimension | MVP scope |
|-----------|-----------|
| **Tenancy** | **One** project (or workspace) end-to-end. |
| **Document type** | **One** document kind (e.g. `memory` or a single `document_key` agreed in API). |
| **Task type** | **One** execution job type (e.g. `llm.echo` or `llm.summarize_document`) with a fixed JSON schema. |
| **Sync** | Local file change for that document → **sync daemon** → cloud API → **Postgres** row updated with version / ETag. |
| **Dashboard** | Read the same row; show revision and content (or hash + preview). |
| **Execution** | User or system enqueues **one** job referencing the document version; **execution worker** runs engine → writes **result** + **events** (success/failure). |
| **Traceability** | Every step emits outbox events: `DocumentPatched`, `JobEnqueued`, `JobStarted`, `JobCompleted` / `JobFailed`. |

**Non-goals for MVP:** full orchestrator DAG, multi-document sync, Gmail, legacy `tasks.json` import parity, SQLite as peer to Postgres.

---

## 7. Open decisions

| # | Topic | Options / tension |
|---|--------|---------------------|
| 1 | **Local cache technology** | Pure files + manifest vs embedded local DB for offline queue. |
| 2 | **Conflict policy v1** | LWW with server version vs three-way merge for markdown. |
| 3 | **Blob storage** | Postgres bytea for MVP vs S3-compatible object store for large artifacts. |
| 4 | **Auth for daemon** | API key long-lived vs OAuth device flow vs mTLS. |
| 5 | **Catalog packaging** | Monorepo `catalog/` vs versioned packages fetched at deploy time. |
| 6 | **Orchestrator placement** | Same binary as API vs separate service from day one. |
| 7 | **Job transport** | Postgres `SKIP LOCKED` job table vs external queue (SQS/NATS). |
| 8 | **Legacy strangler** | Whether `agent-system-base` remains a compatibility shim and for how long. |

---

## Consequences

- All new code must cite **this ADR** and the **SoT matrix** when introducing writers or caches.
- Violations of §4 are **merge-blocking** unless explicitly tagged as `legacy-exception` with an expiry ADR.

## References

- [0002-source-of-truth-matrix.md](./0002-source-of-truth-matrix.md) — per-resource ownership matrix.
- [0003-repository-structure.md](./0003-repository-structure.md) — monorepo folders, apps, packages, CI enforcement.
- [0004-event-model.md](./0004-event-model.md) — event taxonomy, outbox, projections, replay.
- [0005-synchronization-protocol.md](./0005-synchronization-protocol.md) — sync lifecycle, manifest, conflicts, guarantees.
