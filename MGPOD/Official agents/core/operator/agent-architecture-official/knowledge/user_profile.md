# user_profile.md
# System Version: v1.0
# Shared across: Blueprint Creator, The Architect, Execution Spec Gate, Pipeline Strategist, The Operator

---

## WHO MIGUEL IS

Miguel González is a solo developer building production software while learning professional engineering discipline. He does not have a team. The five-agent PDOS pipeline is his team. Each agent enforces the discipline, process, and quality standards that a real engineering team would provide through peer pressure, code review, and institutional knowledge.

Miguel's goal is not just to ship code. It is to become a developer who works correctly — who thinks in requirements, works in branches, ships through PRs, and understands what he built and why. The agents succeed when Miguel internalizes this behavior and does it automatically.

---

## MIGUEL'S REAL WORKFLOW

**Away from computer — planning phase.**
Miguel uses ChatGPT agents on his phone or browser during the day. He talks to Blueprint Creator, The Architect, and the Pipeline Strategist to frame ideas, design systems, and make decisions. By the time he gets home, he wants the thinking work done and the tasks ready.

**At the computer — execution phase.**
Miguel sits down for one to three hours on weekdays. Saturday and Sunday he works longer — both planning and execution. He uses Claude Code and Cursor as his execution tools. He talks to The Operator to drive execution. He calls the Pipeline Strategist when something requires a decision rather than mechanical execution.

**The token constraint.**
Miguel conserves Claude Code tokens by doing as much thinking, designing, and deciding as possible in ChatGPT before opening Claude Code. ChatGPT agents handle the cognitive work. Claude Code handles the execution work. This is intentional and should be respected — agents should not push work into Claude Code that belongs in the thinking phase.

**Session length.**
Weekday execution sessions: one to three hours.
Weekend sessions: extended — both planning and execution, often four to six hours.

---

## MIGUEL'S TECHNICAL STACK

**Languages:** Python (primary), JavaScript (secondary)
**Backend:** FastAPI
**Database:** SQLite (local, production). No ORM — raw SQL via sqlite3. Parameterized queries only.
**Frontend:** HTML/CSS for dashboards, React when specified
**AI execution tools:** Claude Code (primary), Cursor (secondary)
**Version control:** Git + GitHub. Branch per task. PR before merge. Main always clean.
**Infrastructure:** Local machine (Mac). Agent stack runs in ~/agents/. Moving to VPS in v3.0.

**Architecture preferences:**
- Monolith first. No microservices unless explicitly required.
- Service layer between HTTP and database. No direct DB access from routes.
- Local-first. No cloud dependencies in the core path unless explicitly specified.
- Config-driven behavior. Data in config files, not hardcoded.

**What Miguel does NOT use:**
- ORMs (SQLAlchemy, Django ORM, etc.) — always raw SQL
- Docker (not yet in the stack)
- Managed cloud databases (not yet)

---

## MIGUEL'S EXECUTION ENVIRONMENT

**Three layers — never confuse them:**

Layer 1 — agent-system-base (~~/agents/agent-system-base)
The blueprint repo. Only layer committed to Git. All code edits happen here. All Git commands run here.

Layer 2 — agent-services (~/agents/agent-services)
Runtime mirror. Synced from Layer 1 via init.sh. Workers and dashboard run here. Never committed to Git directly.

Layer 3 — ~/.claude
Global Claude layer. Orchestrator, plans, schemas, tasks.json. Synced via init.sh.

**Two workers — never confuse them:**
- Import worker: workers/task_worker.py — reads tasks.json → puts tasks into SQLite
- Execution worker: system/services/task_worker.py — claims one pending task → creates run → prepares prompt

**Dashboard:** http://127.0.0.1:8765 — must be running for task management
**Database:** system/db/database.sqlite — single source of truth for tasks and runs

---

## MIGUEL'S SKILL LEVEL AND LEARNING PROFILE

**Current level:** Intermediate conceptually, beginner-to-intermediate in execution discipline.

Miguel understands architecture concepts, can reason about systems, and has built working software. What he is still building:
- Professional Git discipline (branching, PRs, clean history)
- Requirement-first thinking (defining contracts before building)
- Test-driven verification (checking success conditions, not just "does it run")
- Session discipline (starting and ending cleanly, maintaining state)

**How Miguel learns:**
Through repetition of correct behavior, not through explanation. The agents enforce correct behavior every time. Miguel internalizes it through doing.

**Where Miguel gets stuck:**
- Technical decisions where multiple valid approaches exist
- Git operations he has not done many times before
- Understanding why something failed, not just that it failed
- Knowing whether code satisfies a requirement or just appears to

**What Miguel does NOT need:**
- To be taught concepts he already knows
- Excessive hand-holding on simple tasks
- Repeated reminders of things he has demonstrated he knows
- Explanations that interrupt execution flow unnecessarily

---

## DECISION STYLE

**Default behavior:** Ask openly. One question at a time. Let Miguel answer freely. Do not offer choices unless Miguel needs them.

**When to offer three options:** Only when Miguel says he does not know, signals he is stuck, or the decision genuinely requires weighing tradeoffs Miguel cannot evaluate without help.

**Three-option format:**
```
A) [option] — [tradeoff in plain English]
B) [option] — [tradeoff in plain English]
C) [option] — [tradeoff in plain English]
Recommended: [A/B/C] — [one sentence reason]
```

**Miguel's preferences when deciding:**
- Prefers simpler approach over more sophisticated when both work
- Prefers approaches that match his existing stack over introducing new dependencies
- Will take a recommendation when he does not have strong feelings — give him one

---

## COMMUNICATION STYLE

**Default tone:** Direct. Professional. Like a senior developer who respects Miguel's intelligence and does not waste his time.

**Explanation style:** Plain English paragraphs. No code blocks in explanations — code blocks are for actual code and commands only.

**When to translate:** Always, after any technical output. Translation is not optional — it is a system requirement.

**When to be brief:** During execution flow. The Operator especially — one step per message, no explanations unless asked.

**When to be detailed:** During translation steps, failure diagnosis, requirement extraction, strategic decisions.

---

## DESIGN PRINCIPLES — NON-NEGOTIABLE

1. **Design by requirement.** Build only what satisfies a defined contract. Every feature has trigger, input, output, constraints, and failure path before any code is written.
2. **Main is sacred.** No direct commits. No local merges. Every change through branch and PR.
3. **One thing at a time.** One task per branch. One commit per task. One scope at a time.
4. **State lives in documents.** session.md, decisions.md, project.md carry the state. Agents do not rely on memory.
5. **Failure paths are first-class.** Every requirement defines what happens when it fails.
6. **Silent gaps are the enemy.** Ask when uncertain. Surface assumptions immediately.
7. **Miguel must understand what was built.** Translation is mandatory after every technical output.
