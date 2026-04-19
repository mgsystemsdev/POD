# Agent definitions

Each `*.json` file describes one **logical agent** mapped to a `.claude/skills/<skill>/SKILL.md` playbook.

- **`name`**: stable id; output files use `<name>.output.json`.
- **`tools_preferred` / `tools_fallback`**: used by `orchestrator/tool_validation.py` to pick a strategy.
- **`reads_prior_outputs`**: orchestrator injects prior validated JSON into `context_for_<agent>.json`.

Executable plans live in `agents/plans/*.json` (dependency graph + I/O paths).

Run the controller:

```bash
python -m orchestrator --plan swarm_research --goal "Smoke test" --mode simulate
```

See `orchestrator/README.md`.
