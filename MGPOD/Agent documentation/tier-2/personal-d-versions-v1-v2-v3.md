# The three versions (V1, V2, and V3) of the Personal D

## Overview

V1, V2, and V3 are a **phased roadmap** for the Personal Developer OS: from a manual, local-first loop to an always-on stack. Principle: **prove the system at scale 1 before scaling to 24/7**.

---

## V1 — Local manual (MVP)

### Purpose

Prove the **local execution cycle** end-to-end: project truth, task state, and Git discipline under one operator.

### Operating model

| Aspect | Description |
| :--- | :--- |
| **The bridge** | Operator manually carries baton files between components. |
| **Thinking layer** | Four ChatGPT agents (Architect, Spec Gate, Strategist, Operator) produce Markdown/JSON into `.claude/context/`. |
| **Sync** | Operator runs `agents push` to mirror disk → SQLite. |
| **Execution** | Claude Code or Cursor, guided by Operator GPT. |

### Success criteria

- Session startup under ~2 minutes.
- Three full cycles with **zero** manual patching between steps.

### Constraint

No new automation until the manual loop is fully understood.

---

## V2 — Ngrok bridge (remote convenience)

### Purpose

Let conversational agents **read/write via API** while the laptop is on—less manual copying, more continuity from phone or secondary devices.

### Mechanism

- **ngrok** (or similar) exposes local FastAPI on a public URL.

### Operating model

| Aspect | Description |
| :--- | :--- |
| **Direct API** | ChatGPT custom actions `POST`/`GET` project state. |
| **Hybrid handoff** | Less reliance on manual `agents push` for some flows; Architect/Spec Gate may write via API. |
| **Security** | API key middleware + CORS before exposing the API. |

### Limitation

Works only while the laptop is on and the tunnel is active.

---

## V3 — VPS 24/7 (always-on OS)

### Purpose

**Always-on** control plane: work can progress without the local machine online.

### Mechanism

- Deploy FastAPI, SQLite, and workers to a Linux **VPS**.

### Operating model

| Aspect | Description |
| :--- | :--- |
| **Workers** | `task_worker`, `decision_reviewer`, etc. on **cron** on the server. |
| **Device independence** | e.g. design on phone in the morning; desk session sees tasks/blueprints already processed. |
| **Persistence** | DB is the central nervous system; reachable from any client. |

### Deployment requirements

- Stable hostname, **HTTPS** (e.g. Let’s Encrypt), **systemd** supervision, **daily backups** of SQLite.

### Final goal

Agents advise and workers transport; **the human gate** stays explicit at every critical decision.

---

## Summary table

| Version | Mode | Infra | Key idea |
| :--- | :--- | :--- | :--- |
| **V1** | Local, manual bridge | Laptop only | Prove the loop |
| **V2** | Remote API while online | Laptop + tunnel | Reduce friction |
| **V3** | 24/7 | VPS | Always-on mirror + workers |
