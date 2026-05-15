# `agents` workspace

This directory groups related repositories for Miguel’s agent and PDOS tooling.

| Path | Role |
|------|------|
| **`agent-system-base/`** | **Blueprint (source of truth)** — orchestrator, agent JSON, schemas, workers, dashboard, `init.sh`. Edit and commit here. |
| **`MGPOD/`** | **PDOS documentation** — official prompts, knowledge trees, and tiered docs for the Personal Developer OS. No runtime code. |
| **`~/agents/agent-services/`** (on your machine) | **Runtime mirror** — created/updated by `init.sh`; do not treat as the git source of truth. |
| **`~/.claude/`** (on your machine) | **Global Claude layer** — receives `orchestrator/`, `agents/`, and `schemas/` from `init.sh`. |

## What to run after blueprint changes

```bash
bash ~/agents/agent-system-base/init.sh /path/to/your-active-project
```

Use a real project root (not a doc placeholder). Cron and install scripts ship from **`agent-system-base`** and sync into **`agent-services`**.

## More reading

- Execution stack and task schema: [`agent-system-base/CLAUDE.md`](agent-system-base/CLAUDE.md)
- Day-to-day commands: [`agent-system-base/OPERATOR_GUIDE.md`](agent-system-base/OPERATOR_GUIDE.md)
- PDOS prompts and authority model: [`MGPOD/CLAUDE.md`](MGPOD/CLAUDE.md)
- Workspace architecture (domain / application / infrastructure): [`docs/architecture.md`](docs/architecture.md)
