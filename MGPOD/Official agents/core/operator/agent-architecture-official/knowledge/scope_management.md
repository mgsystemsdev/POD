# Scope Management — The Operator

Run this after session start (step 10) and before any task execution.

---

## SCOPE ASSESSMENT

Ask: "Open dashboard. List all pending tasks."

Build a scope map:
- Total tasks
- Distinct scopes
- Dependencies (what must complete before what)
- What each task produces for the next task

**PRD ALIGNMENT CHECK:**
Ask: "Has implementation drifted from the PRD? Update it before we execute."

Reflect the map to Miguel. Wait for confirmation.

---

## SCOPE TYPES — HOW TO HANDLE EACH

**STANDALONE (one task, no dependencies):**
One branch. Full close-out cycle. Done.

**SCOPE (multiple dependent tasks):**
Execute in dependency order. Carry cumulative context between tasks. Pause the entire scope on a failed verify — do not continue until the failing task passes.

**MULTIPLE SCOPES:**
Complete one scope fully before starting the next. Never mix branches from different scopes.

---

## SCOPE QUESTION

After reflecting the map: "Which scope or task first?"

Wait for Miguel's answer before proceeding to TASK READINESS CHECK.
