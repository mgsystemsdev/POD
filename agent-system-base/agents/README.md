# Agent definitions

Each `*.json` file describes one **logical agent** mapped to a `.claude/skills/<skill>/SKILL.md` playbook.

- **`name`**: stable id; output files use `<name>.output.json`.
- **`tools_preferred` / `tools_fallback`**: used by `orchestrator/tool_validation.py` to pick a strategy.
- **`reads_prior_outputs`**: orchestrator injects prior validated JSON into `context_for_<agent>.json`.

Executable plans live in `agents/plans/*.json` (dependency graph + I/O paths). Plan ids on disk include **`swarm_research`**, **`linear_context_research`**, **`feature_build`**, **`bug_fix`**, and **`review_wave`** (hardening: devil-advocate, security-reviewer, drift-detector → merge → `review_merged.json`).

Run the controller from **`~/.claude`** after `init.sh`, with a writable run directory:

```bash
cd ~/.claude && python3 -m orchestrator \
  --runs-dir /path/to/your-project/runs/ephemeral \
  --plan swarm_research \
  --goal "Smoke test" \
  --mode simulate
```

Step outputs are validated as **v2** envelopes (see `schemas/README.md` and `orchestrator/README.md`).

See `orchestrator/README.md`.
