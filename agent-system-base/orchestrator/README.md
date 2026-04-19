# DMRB agent orchestrator

Runnable controller over **plans** (`agents/plans/*.json`), **agent defs** (`agents/*.json`), and the **mandatory output schema** (`schemas/agent_output.schema.json`).

## Prerequisites

- Python **3.10+** (`python3`)
- Shell **cwd** = repo root (`DRMB_PROD`), so `python3 -m orchestrator` resolves the package.

## Commands

### Full simulate (no Claude session required)

```bash
python3 -m orchestrator --plan swarm_research --goal "Your task" --mode simulate
```

Prints `runs/ephemeral/<uuid>`. Inspect `merged.json` and per-agent `*.output.json`.

### Handoff (wave-by-wave with Claude Code)

```bash
python3 -m orchestrator --plan swarm_research --goal "Your task" --mode handoff
```

1. Complete JSON for wave 0 (e.g. `context.output.json`) using `context_for_context.json` + skill `.claude/skills/context/SKILL.md`.
2. Advance:

```bash
python3 -m orchestrator --resume <run_id> --advance
```

3. Repeat until the merge wave runs, **or** when every `*.output.json` exists:

```bash
python3 -m orchestrator --resume <run_id> --finish
```

### Reuse validated outputs (dedupe)

```bash
python3 -m orchestrator --plan swarm_research --goal "Same task" --mode simulate --reuse-outputs
```

Skips a step when the output file already validates.

## Tool validation

The orchestrator probes **Bash**, **WebFetch** (HTTP to `example.com`), and treats **WebSearch** as unavailable unless overridden:

```bash
export DMRB_AGENT_TOOLS="WebSearch=1,WebFetch=0"
```

Fallback notes are injected into each simulated envelope’s `decisions[]` and `HANDOFF_*.json`.

## Failure model

- Each agent step: **one retry** on unexpected errors, then a **valid failure envelope** is written (still matches required keys).
- Builtin merge: same retry policy.
- Workflow **continues**; check `run_state.json` → `errors`.

## Layout

| Path | Role |
|------|------|
| `agents/` | Agent metadata + tool preferences |
| `agents/plans/` | DAG steps, `depends_on`, `parallel_group`, I/O files |
| `schemas/agent_output.schema.json` | JSON Schema (mirrored by `orchestrator.models.validate_agent_output`) |
| `runs/ephemeral/` | Active logs (gitignored) |
| `runs/examples/` | Committed samples |

## Plans

- `swarm_research` — context → parallel(research, create) → `merged.json`
- `linear_context_research` — context → research only
