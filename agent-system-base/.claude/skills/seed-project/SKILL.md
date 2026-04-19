---
name: seed-project
version: "1.0.0"
description: >
  Seed a new project with the global orchestrator and project management tools from
  ~/agents/agent-system-base/. Trigger when: "set up a new project", "initialize project tools",
  "seed this project", or when working in a project that lacks claude-system/ or system/.
allowed-tools: Bash, Read, Glob
---

# Seed Project

Sets up claude-system/ (agent orchestrator) and system/ (dashboard + scripts) in the target project.

## Steps

1. Confirm the target project directory with the user
2. Check if already seeded: look for claude-system/ and system/ at the target root
3. Run: `bash ~/agents/agent-system-base/init.sh <target-project-dir>`
4. Report exactly what was created
5. Confirm the orchestrator works: `cd <target>/claude-system && python3 -m orchestrator --plan swarm_research --goal "smoke test" --mode simulate`
