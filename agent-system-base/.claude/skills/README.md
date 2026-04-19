# Claude Code skills (this repo)

Project-local skills live here: `.claude/skills/<skill-name>/SKILL.md`. They apply when you use **Claude Code** in this repository and typically override global skills of the same name in `~/.claude/skills/`.

| Skill     | Use when |
|-----------|----------|
| `create`  | User wants a new reusable skill/agent pattern |
| `context` | Need current docs or API behavior before coding |
| `swarm`   | Executable DAG + `cd claude-system && python3 -m orchestrator` (see `claude-system/agents/plans/`, `claude-system/orchestrator/README.md`) |
| `research`| Multi-source technical investigation |

**Experimental agent teams:** set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in the environment that launches `claude`, then restart. Parallel orchestration still needs clear plans and shared output paths (see `swarm`).

See this project's CLAUDE.md for project rules; skills add workflow playbooks on top of that.
