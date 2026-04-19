# Vertical data flow — full system

End-to-end views of the MGPOD / agent-system stack: [This framework outlines](../tier-1/this-framework-outlines.md), [Personal D V1–V3](../tier-2/personal-d-versions-v1-v2-v3.md), [4 ChatGPT agents](../tier-3/chatgpt-agents-thinking-layer.md), and tier-2 operational docs.

**Vertical** means top-to-bottom: thinking → authored disk truth → sync → SQLite mirror → dashboard/workers → execution tools → git, with human gates. **V1 / V2 / V3** are deployment phases on the same conceptual stack, not three different architectures.

---

## 1. Seven layers (compact overview)

Authored knowledge flows **down** into the control plane; execution produces code and evidence in **version control**. The database **mirrors** disk; it does not replace `.claude/context/`.

```mermaid
flowchart TB
  subgraph L1["Layer 1 — Thinking"]
    A["ChatGPT agents: Blueprint Creator (GPT-0) / Architect (GPT-1) / Spec Gate (GPT-2) / Pipeline Strategist (GPT-3, on-call) / Operator (GPT-4)<br/>Aux agents (7): Aux Strategist · Senior Dev · DB Specialist · Backend · Schema · UI · System Design"]
  end

  subgraph L2["Layer 2 — Knowledge (disk)"]
    K[".claude/context/<br/>project.md · tasks.json · session.md · decisions.md · MEMORY.md"]
  end

  subgraph L3["Layer 3 — Sync"]
    S["agents push<br/>sync_worker + import_worker"]
  end

  subgraph L4["Layer 4 — Data (SQLite)"]
    D["database.sqlite<br/>projects · tasks · runs · blueprints · decisions · session_logs · proposed_actions · memory"]
  end

  subgraph L5["Layer 5 — Control plane"]
    UI[Dashboard :8765]
    W[Workers: task_worker · decision_reviewer]
  end

  subgraph L6["Layer 6 — Execution"]
    E[Claude Code · Cursor<br/>thin adapters → Layer 2]
  end

  subgraph L7["Layer 7 — Version control"]
    G[Git / GitHub<br/>branch per task · PR merge]
  end

  L1 -->|"structured MD + JSON<br/>(manual handoff V1)"| L2
  L2 -->|"disk → DB only"| L3
  L3 --> L4
  L4 <--> UI
  L4 <--> W
  W -->|"enriched prompts"| L6
  L6 -->|"edits + evidence"| L7
  L6 -.->|"same grounding"| L2
```

---

## 2. End-to-end pipeline (contracts → execution → verification)

Aligned with [Architect pipeline](prompt/architect.md): Blueprint Creator (draft bundle) → Architect → Execution Spec Gate (`tasks.json`) → Operator → execution → verification (evidence vs `success_criteria`; subjective claims invalid).

```mermaid
flowchart TB
  subgraph L1["Layer 1 — Thinking (ChatGPT)"]
    direction TB
    ARCH["Architect: Section A + Section B + schema.json<br/>modes ASK / GUIDE / BLOCK · one question/turn"]
    SG["Execution Spec Gate: Section B → tasks.json<br/>validate · generate · translate · BLOCK/ASK on gaps"]
    STRAT["Strategist: on-call · decisions.md · tool-tagged prompts"]
    OPR["Operator GPT: session discipline · session.md"]
    ARCH --> SG
    STRAT -.->|when blocked| OPR
    OPR -.->|drives| EXEC_LOCAL
  end

  subgraph L2["Layer 2 — Knowledge disk (source of truth)"]
    CTX[".claude/context/<br/>project.md · tasks.json · session.md · decisions.md · MEMORY.md"]
  end

  subgraph L3["Layer 3 — Sync"]
    PUSH["agents push<br/>sync_worker: *.md → mirror tables<br/>import_worker: tasks.json → tasks (atomic)"]
  end

  subgraph L4["Layer 4 — SQLite operational mirror"]
    DB[("projects · tasks · runs · blueprints · decisions · session_logs · proposed_actions · memory")]
  end

  subgraph L5["Layer 5 — Control plane"]
    UI["Dashboard :8765 · FastAPI<br/>observe + Actions approve/reject"]
    W["task_worker · decision_reviewer<br/>claim task · build prompt · runs row"]
  end

  subgraph L6["Layer 6 — Execution tools"]
    EXEC_LOCAL["Claude Code / Cursor<br/>adapters point at Layer 2"]
  end

  subgraph L7["Layer 7 — Version control"]
    GIT["Git/GitHub · branch per task · PR merge"]
  end

  ARCH --> CTX
  SG --> CTX
  STRAT --> CTX
  OPR --> CTX

  CTX --> PUSH
  PUSH --> DB
  DB <--> UI
  DB <--> W
  W --> EXEC_LOCAL
  EXEC_LOCAL --> GIT
  EXEC_LOCAL -.->|same grounding| CTX

  VERIFY["Verification: evidence vs success_criteria + contract"]
  EXEC_LOCAL --> VERIFY
```

---

## 3. Layer 1 detail — four roles + Spec Gate internals

**Architect** produces requirement contracts and Section B. **Execution Spec Gate** is a mechanical translator and quality gate (see [spec_gate.md](../spec-gate/prompt/spec_gate.md), [gap_handling.md](../spec-gate/knowledge/gap_handling.md)).

```mermaid
flowchart TB
  subgraph Architect["Architect"]
    A1[Idea / update request]
    A2["Per-REQ: Trigger · Input · Output · Constraints · Failure path · Done when"]
    A3["Pre-output: Spec Gate sim · Execution sim · Verification sim"]
    A4["Emit: Section A + Section B + schema.json"]
    A1 --> A2 --> A3 --> A4
  end

  subgraph SpecGate["Execution Spec Gate"]
    S0[Input: full Section B Markdown]
    S1["Validate: 10 sections · REQ 5/5 + Done when<br/>wrong shape → BLOCK wrong_input_shape"]
    S2["Task generation: 1 task ↔ 1 requirement_ref<br/>30–90m atomic · infra-first · depends_on DAG"]
    S3["Each task: 8 keys — id title description success_criteria failure_behavior requirement_ref tier depends_on"]
    S4["description blocks: OBJECTIVE · REQUIREMENT · ARCH CONSTRAINTS · DONE WHEN · FAILURE · DO NOT"]
    S5{Gap?}
    S6[BLOCK JSON → return_to Architect]
    S7["ASK: one question OR 3 options A/B/C"]
    S0 --> S1 --> S2 --> S3 --> S4 --> S5
    S5 -->|critical| S6
    S5 -->|fork/ambiguity| S7
    S5 -->|ok| OUT[tasks.json array]
  end

  subgraph Strategist["Strategist"]
    T1[Trigger: stuck · PRD hole · confusing tool output]
    T2[3 options + tradeoffs + recommendation]
    T3["decisions.md · CLAUDE_CODE / CURSOR_ASK prompts"]
  end

  subgraph OperatorGPT["Operator GPT"]
    O1[Pick highest-priority task from dashboard state]
    O2[Execute → Verify → Translate → Review → Commit → Next]
    O3["session.md continuity · branch per task · no direct main"]
  end

  A4 --> S0
  S6 -.->|fix contract| A4
  S7 -.->|user answers| S0
  OUT --> SAVE[Save to .claude/context/]
  T3 --> SAVE
  O3 --> SAVE
```

---

## 4. V1 / V2 / V3 — same stack, different attachment

Phased roadmap: prove at scale 1, then remote API, then 24/7 VPS ([Personal D versions](../tier-2/personal-d-versions-v1-v2-v3.md)).

```mermaid
flowchart LR
  subgraph Common["Shared core"]
    L2[Layer 2 disk]
    SYNC[agents push]
    SQL[(SQLite)]
    DASH[Dashboard + workers]
    EX[Claude Code / Cursor]
  end

  subgraph V1["V1 — local manual"]
    GPT1[4 ChatGPT agents]
    BAT[Operator carries baton files]
    GPT1 --> BAT --> L2
  end

  subgraph V2["V2 — laptop on + tunnel"]
    GPT2[ChatGPT + custom actions]
    API["FastAPI via ngrok HTTPS<br/>API key + CORS"]
    GPT2 --> API
    API -.->|read/write some state| SQL
    L2 -.->|hybrid: less copy| API
  end

  subgraph V3["V3 — VPS 24/7"]
    VPS["FastAPI + SQLite + workers<br/>systemd · cron · HTTPS · backups"]
    GPT3[Any client / phone / desk]
    GPT3 --> VPS
  end

  L2 --> SYNC --> SQL --> DASH --> EX
```

---

## 5. Vertical slice — one task from `tasks.json` to done

```mermaid
sequenceDiagram
  participant Disk as .claude/context tasks.json
  participant Push as agents push import_worker
  participant DB as SQLite tasks runs
  participant W as task_worker
  participant Tool as Claude Code Cursor
  participant API as Dashboard API
  participant Op as Operator

  Disk->>Push: ingest atomic batch
  Push->>DB: upsert tasks
  W->>DB: claim pending depends_on satisfied WIP=1
  W->>DB: task in_progress run pending_input
  W->>Tool: enriched prompt blueprint decisions session
  Tool->>Op: implement verify evidence
  Op->>API: POST task complete
  API->>DB: done run success
  Note over Disk,DB: Files authoritative mirror rule DB does not overwrite context md
```

---

## 6. Operational slice (flowchart)

Typical path from mirrored state through dashboard, workers, and git.

```mermaid
flowchart TB
  subgraph Disk["Project disk"]
    PM[project.md]
    TJ[tasks.json]
    SM[session.md · decisions.md]
  end

  subgraph Sync["Sync CLI"]
    PUSH[agents push]
  end

  subgraph DB["SQLite mirror"]
    T[(tasks)]
    R[(runs)]
    B[(blueprints)]
    PA[(proposed_actions)]
  end

  subgraph Plane["Dashboard + workers"]
    API[FastAPI]
    TW[task_worker]
    ACT[Actions tab — approve / reject]
  end

  subgraph Exec["Execution"]
    CC[Claude Code / Cursor]
  end

  PM --> PUSH
  TJ --> PUSH
  SM --> PUSH
  PUSH --> B
  PUSH --> T

  TW --> T
  TW --> R
  TW --> CC

  API --> T
  API --> PA
  PA --> ACT
  ACT -->|approved writes| T

  API -->|POST …/complete| T
  API --> R

  CC -->|PR + proof| GH[GitHub]
```

---

## 7. Proposed-actions gate (agent writes)

Internal agents stage changes; humans commit them to operational tables after review ([SQLite operational mirror](../tier-2/sqlite-operational-mirror.md)).

```mermaid
sequenceDiagram
  participant Agent as Internal agent
  participant DB as SQLite
  participant UI as Dashboard Actions
  participant Op as Operator

  Agent->>DB: insert proposed_actions (pending)
  UI->>DB: read pending
  Op->>UI: review payload
  Op->>DB: approve → commit to primary tables
  Note over DB: DB does not overwrite .claude/context/
```

---

## Related docs

- [Sync layer](../tier-2/sync-layer.md) — registry, artifacts, task ingestion.
- [Workers operational bridge](../tier-2/workers-operational-bridge.md) — `--import`, `--execute`, decision reviewer.
- [Dashboard FastAPI](../tier-2/dashboard-fastapi-backend.md) — APIs, observe vs control.
- [Architect prompt](prompt/architect.md) — contract and validation simulations.
- [Execution Spec Gate prompt](../spec-gate/prompt/spec_gate.md) — Section B → `tasks.json` rules.
