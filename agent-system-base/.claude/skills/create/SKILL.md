---
name: create
version: "1.0.0"
description: >
  Create new skills or agents. Trigger this proactively when a repeatable workflow, multi-step
  pattern, or autonomous task is identified during conversation — even if the user does not
  explicitly ask. Also trigger when the user says "make a skill", "create an agent", "turn this
  into a skill", "automate this", "save this workflow", or "I keep doing this". If a workflow
  has been executed twice in a conversation, suggest capturing it as a skill or agent.
allowed-tools: Read, Write, Grep, Glob, Bash
---

# Skill & Agent Creator

Orchestrate the creation of reusable skills and agents for Claude Code. The core job is making
the right orchestration decisions — type, placement, tools, model, scope — then writing a
clean artifact.

## Decision 1: Skill or Agent?

Count how many of these agent signals are present. If 2 or more match, create an agent.
If 0-1 match, create a skill.

- Needs its own context window (large codebase scan, parallel work)
- Runs autonomously without user interaction
- Needs to invoke other skills
- Would benefit from a different model or temperature
- Performs a distinct role (reviewer, researcher, deployer)

## Decision 2: Global or Project?

- If it's useful across multiple projects → `~/.claude/skills/<name>/` or `~/.claude/agents/`
- If it depends on project-specific files, paths, or architecture → `.claude/skills/<name>/` or `.claude/agents/`
- When in doubt, ask the user

## Decision 3: Tools

Only grant tools the skill actually needs:
- Read, Grep, Glob — for analysis-only skills
- Add Write — if it creates/modifies files
- Add Bash — if it runs commands
- Add WebSearch, WebFetch if it needs external info

## Output

Create the SKILL.md (or agent .md) with:
1. Clean YAML frontmatter (name, description, allowed-tools)
2. Clear trigger conditions in the description
3. Step-by-step instructions in the body
4. Any templates or examples as separate files in the skill directory if needed

After creating, confirm the file path and suggest testing it.
