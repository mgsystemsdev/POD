# CLAUDE.md — agent-system-base

This is the source-of-truth repo for Miguel's AI orchestration system.
Claude Code reads this file in every session opened inside this directory.

---

## Three-Folder Architecture

| Folder | Role |
|--------|------|
| `~/agents/agent-system-base/` | **Blueprints** — you edit here. Nothing runs directly from here. |
| `~/.claude/` | **Global State** — Claude Code's domain. Skills/agents live here natively. |
| `~/agents/agent-services/` | **Runtime** — workers, crons, logs, API keys. |

`init.sh` syncs blueprints → global state + runtime. Run it after any change to skills, agents, orchestrator, or workers.

**What `init.sh` copies:** `orchestrator/`, `agents/`, and `schemas/` → `~/.claude/`; `workers/`, `system/`, and `config/` → `~/agents/agent-services/`. The `system/` tree is **not** copied into `~/.claude/` (if you see a script banner that implies otherwise, trust the `rsync` lines in `init.sh`).

**Monorepo map (domain / application / infrastructure):** see [`docs/architecture.md`](../docs/architecture.md) at the workspace root. **Historical system audits:** [`docs/audits/`](../docs/audits/).

---

## Task Schema

All tasks in `~/.claude/tasks.json` must follow this schema. Required fields: `task_id`, `title`, `status`, `priority`, `action_type`.

```json
{
  "task_id": "ses-YYYYMMDD-NNN",
  "title": "imperative phrase under 60 chars",
  "description": "one sentence — what done looks like",
  "priority": 1,
  "status": "pending",
  "action_type": "claude_execute",
  "action_payload": {
    "prompt": "full self-contained instructions with all context"
  },
  "correlation_id": "uuid4 — shared by all tasks in one planning session",
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601"
}
```

**action_type values:**
- `claude_execute` — invoke Claude CLI autonomously
- `run_plan` — trigger an orchestrator plan
- `run_script` — execute a script in the project directory
- `generate_file` — create or overwrite a file
- `log_only` — record a message, no side effects

**priority:** 1 = critical, 2 = high, 3 = medium, 4 = low, 5 = backlog

---

## Skill Authoring Rules

Every skill must have:
- `~/agents/agent-system-base/.claude/skills/<name>/SKILL.md`
- `~/agents/agent-system-base/agents/<name>.json` (agent definition — required pairing)
- Frontmatter: `name`, `description`, `version`, `allowed-tools`
- Body under 500 lines; use `references/` for overflow

Frontmatter template:
```yaml
---
name: skill-name
version: "1.0.0"
description: >
  One paragraph. Include WHEN to trigger (specific phrases, contexts).
  Be slightly pushy — Claude undertriggers skills by default.
allowed-tools: Read, Grep, Glob
---
```

After creating a skill, run `init.sh` to sync it to `~/.claude/skills/`.

---

## Agent Definition Rules

Every `agents/<name>.json` must have:
- `name` — matches the skill name exactly
- `description` — one sentence
- `skill` — skill name (enables skill loader in orchestrator execute mode)
- `tools_preferred` — list of tools this agent uses
- `critical` — true if failure should abort the plan
- `output_format` — always `"agent_output_v2"`

---

## Orchestrator Usage

```bash
# Dry run (no API calls)
cd ~/.claude && python3 -m orchestrator \
  --runs-dir <project>/runs/ephemeral \
  --plan swarm_research \
  --goal "your goal here" \
  --mode simulate

# Execute (requires ANTHROPIC_API_KEY)
cd ~/.claude && python3 -m orchestrator \
  --runs-dir <project>/runs/ephemeral \
  --plan swarm_research \
  --goal "your goal here" \
  --mode execute
```

Plans live in `agents/plans/`. Available: `swarm_research`, `linear_context_research`, `feature_build`, `bug_fix`.

Agent outputs must conform to `schemas/agent_output_v2.schema.json`.

---

## File Conventions

- Files over 300 lines should be split
- Commit messages: imperative mood, under 72 chars (e.g. `add: planner skill`)
- Never commit `.env` files
- `runs/` and `__pycache__/` are gitignored

---

## After Any Change

```bash
bash ~/agents/agent-system-base/init.sh /path/to/current-project
```

This keeps `~/.claude/` and `~/agents/agent-services/` in sync with this repo.
