# Agent orchestrator

Runnable controller over **plans** (`agents/plans/*.json`), **agent defs** (`agents/*.json`), and the **validated agent output envelope** used at simulate/execute time.

## Prerequisites

- Python **3.10+** (`python3`)
- After `init.sh`, run with **`cwd`** = `~/.claude` so `python3 -m orchestrator` resolves the synced package. Always pass **`--runs-dir`** to a project’s `runs/ephemeral` (or another writable run root).

## Output validation (v2)

Simulate and execute paths validate each step’s JSON with **`orchestrator.models.validate_agent_output_v2`**, using rules aligned with **`schemas/agent_output_v2.schema.json`**.

The file **`schemas/agent_output.schema.json`** remains the base envelope; v2 adds fields such as `run_id`, `step_id`, and stricter shape checks. Agent JSON files may reference the v1 schema path in `inputs_schema` / `output_schema`; runtime validation is still v2.

## Commands

### Full simulate (no Claude session required)

```bash
cd ~/.claude && python3 -m orchestrator \
  --runs-dir /path/to/your-project/runs/ephemeral \
  --plan swarm_research \
  --goal "Your task" \
  --mode simulate
```

Prints `runs/ephemeral/<uuid>` under `--runs-dir`. Inspect `merged.json` (or plan-specific merge output) and per-agent `*.output.json`.

### Handoff (wave-by-wave with Claude Code)

```bash
cd ~/.claude && python3 -m orchestrator \
  --runs-dir /path/to/your-project/runs/ephemeral \
  --plan swarm_research \
  --goal "Your task" \
  --mode handoff
```

1. Complete JSON for wave 0 (e.g. `context.output.json`) using `context_for_context.json` + skill under `~/.claude/skills/` (or project `.claude/skills/` where applicable).
2. Advance:

```bash
cd ~/.claude && python3 -m orchestrator --resume <run_id> --advance
```

3. Repeat until the merge wave runs, **or** when every `*.output.json` exists:

```bash
cd ~/.claude && python3 -m orchestrator --resume <run_id> --finish
```

### Reuse validated outputs (dedupe)

```bash
cd ~/.claude && python3 -m orchestrator \
  --runs-dir /path/to/your-project/runs/ephemeral \
  --plan swarm_research \
  --goal "Same task" \
  --mode simulate \
  --reuse-outputs
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
- Workflow **continues**; check `run_state.json` → `errors`. Steps with **`critical: true`** in the agent definition abort the run on failure (see `orchestrator/controller.py`).

## Layout

| Path | Role |
|------|------|
| `agents/` | Agent metadata + tool preferences |
| `agents/plans/` | DAG steps, `depends_on`, `parallel_group`, I/O paths |
| `schemas/agent_output.schema.json` | Base JSON Schema (shared with `validate_agent_output`) |
| `schemas/agent_output_v2.schema.json` | v2 documentation mirror; **execute/simulate validation** uses `validate_agent_output_v2` |
| `runs/ephemeral/` | Active logs under the project you pass as `--runs-dir` (typically gitignored) |
| `runs/examples/` | Committed samples |

## Plans

| Plan id | Summary |
|---------|---------|
| `swarm_research` | context → parallel(research, create) → `merged.json` |
| `linear_context_research` | context → research only |
| `feature_build` | context → research → create → merge |
| `bug_fix` | context → research → create → merge |
| `review_wave` | parallel(devil-advocate, security-reviewer, drift-detector) → `review_merged.json` |

See `agents/plans/<plan_id>.json` for the authoritative step graph and `description` fields.
