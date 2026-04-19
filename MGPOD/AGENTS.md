# AGENTS.md — [Project Name]
# Instruction file for all AI tools
# Read this file before starting any work
# Applies to: Claude, Cursor, Copilot, Codex, Windsurf, and any AI working in this project

---

## What This File Is

This project runs on a Claude Code operating system with global memory, skills, agents,
hooks, and a review layer. This file explains how that system works so any AI tool can
operate within it correctly.

---

## The Global Brain

All decisions, preferences, and identity live in one place:

```
~/.claude/memory/
├── user.md        ← Who Miguel is, his role, his goals
├── preferences.md ← How he likes to work, coding standards
├── decisions.md   ← Every architectural decision ever made
└── agent_stack.md ← How the agent runtime works
```

**IF YOU ARE NOT CLAUDE:**
Read these files at the start of every session.
Apply everything in them without being asked.
Never contradict a decision in decisions.md.

---

## Available Agents

These agents exist globally in `~/.claude/agents/`.
Any AI tool should replicate this behavior when working in this project:

| Agent | Purpose | When to use |
|-------|---------|-------------|
| researcher | Deep research, cross-referenced | "research this" |
| planner | Break task into steps | "plan this" |
| devil-advocate | Challenge decisions | "push back on this" |
| security-reviewer | Scan for vulnerabilities | "is this safe" |
| drift-detector | Check against original spec | "did we drift" |
| reviewer | Run all hardening agents | "review this" |
| deep-debugger | Deep bug investigation | "debug this" |
| workflow-coach | Improve how we work | "coach me" |

**IF YOU ARE NOT CLAUDE:**
You cannot run these agents natively.
Instead — simulate their behavior:
- Before any significant change: argue against your own proposal (devil-advocate behavior)
- Before shipping: scan for OWASP Top 10 (security-reviewer behavior)
- Before finishing: check your output matches the original request (drift-detector behavior)

---

## Project-Specific Agents

[Auto-populated when project is initialized]
Add agents specific to this project here.

---

## Rules All AI Tools Must Follow

1. Read `~/.claude/memory/` before starting
2. Never contradict `decisions.md`
3. Never store secrets in code
4. Never use ORM if stack is Python + Postgres
5. Always use parameterized SQL
6. Log significant decisions to `decisions.md`
7. Run a mental /review before shipping anything
8. If unsure — ask, don't assume
