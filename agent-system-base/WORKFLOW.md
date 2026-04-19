# WORKFLOW.md — agent-system-base
# Instruction file for all AI tools
# Read this file before starting any work
# Applies to: Claude, Cursor, Copilot, Codex, Windsurf, and any AI working in this project

---

## What This File Is

This is the operating procedure for the agent-system-base repo — the source-of-truth
blueprints for Miguel's AI orchestration system. Changes here propagate to `~/.claude/`
(global state) and `~/agents/agent-services/` (runtime) via `init.sh`.

---

## Session Start — Every Tool, Every Time

Before doing anything:
1. Read `~/.claude/memory/user.md`
2. Read `~/.claude/memory/preferences.md`
3. Read `~/.claude/memory/decisions.md`
4. Read `~/.claude/memory/agent_stack.md`
5. Read this project's `CLAUDE.md`
6. Read `AGENTS.md`
7. Confirm what the current task is
8. Do not start work until steps 1–7 complete

---

## How to Work in This Project

**PLAN BEFORE YOU BUILD**
- State what you are about to do
- Break it into steps
- Get confirmation before executing

**ONE THING AT A TIME**
- Complete one task fully before starting the next
- Do not scope creep mid-task
- If you discover something new — log it, finish current task first

**DECISIONS GET LOGGED**
Any architectural decision made during work must be appended to:
`~/.claude/memory/decisions.md`

Format: date, decision, reasoning, expected outcome, 30-day review date

**BEFORE SHIPPING ANYTHING**
Run this mental checklist:
- [ ] Does this match the original request?
- [ ] Are there hardcoded secrets?
- [ ] Is input validated?
- [ ] Are auth checks present?
- [ ] Does this contradict any past decision?
- [ ] Would a senior engineer approve this?

If any box is unchecked — fix before shipping.

---

## Run Commands

```bash
# Sync blueprints → global state + runtime (run after ANY change)
bash ~/agents/agent-system-base/init.sh /path/to/current-project
```

## Orchestrator Commands

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

Available plans: `swarm_research`, `linear_context_research`, `feature_build`, `bug_fix`

## After Any Change

```bash
bash ~/agents/agent-system-base/init.sh /path/to/current-project
```

This keeps `~/.claude/` and `~/agents/agent-services/` in sync with this repo.

---

## Tool-Specific Notes

**CLAUDE CODE**
- Skills available: /research /review /swarm /create /debug /plan
- Hooks active: lint-on-save, pre-commit, init-project-files
- Memory loads automatically via hook

**CURSOR**
- Read `.cursor/rules/` — memory.mdc loads `~/.claude/memory/`
- Follow AGENTS.md for agent simulation

**COPILOT**
- Read `CLAUDE.md` and this file before suggesting
- Follow the rules in `AGENTS.md`
- When in doubt: suggest, don't auto-apply

**CODEX**
- Read all memory files before executing
- Follow AGENTS.md agent simulation rules
- Log decisions after execution

**WINDSURF**
- Read `CLAUDE.md` and memory files at session start
- Follow workflow steps above
- Apply `preferences.md` coding standards

---

## Queue Architecture

```
SQLite         — single source of truth for ALL tasks, runs, proposed actions, decisions
tasks.json     — optional creation input only (planner output, ChatGPT tasks, etc.)
               — NOT an execution queue; NOT a runtime state store

Import flow:   tasks.json → global worker (import-only) → SQLite tasks (pending)
Exec flow:     SQLite tasks (pending) → SQLite worker → SQLite runs (history)
AI proposals:  AI output (tasks_to_create) → proposed_actions table → human approves via
               dashboard → proposed_action_service executes via task_service

Rule:          No direct DB writes. All writes go through services.
Rule:          AI never writes tasks directly. Always proposes → human approves.
```

---

## When Something Goes Wrong

1. Stop — do not continue building on a mistake
2. Read `decisions.md` — did this contradict a past decision?
3. Log what went wrong to `~/.claude/gotchas.md`
4. Fix the root cause — not just the symptom
5. Continue
