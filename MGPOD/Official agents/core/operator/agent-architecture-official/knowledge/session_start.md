# Session Start Sequence — The Operator

Run this sequence in order at every session start. No step may be skipped or reordered.

---

## STEP 1 — Project identity
Ask: "What project? Path to agent-system-base?"

## STEP 2 — Claude Code availability
Ask: "Is Claude Code available or exhausted?"

## STEP 3 — PRD
Ask: "Paste the PRD or key sections."

## STEP 4 — Architecture confirm
Validate architecture and constraints. Reflect back. "Correct?"

---

## STEP 5 — System state
Ask Miguel to run: `ls system/ workers/` from agent-services.

If system/ or workers/ missing: "Run init.sh first."

```
bash ~/agents/agent-system-base/init.sh /path/to/active-project
```

## STEP 6 — Dashboard
Ask: "Dashboard running?"

If not: `cd ~/agents/agent-services && python3 system/dashboard/server.py`

## STEP 7 — Last task
Ask: "Last completed task? Anything broken or in progress?"

## STEP 8 — Session log
Read `[project-root]/.claude/session.md` last entry.
Cross-reference with Miguel's answer.
If session.md missing: create it now.

---

## STEP 9 — Git state
Ask: "Run: `git status && git log --oneline -5` — paste both."

Then handle the state:

**FIRST-TIME (no .git or no commits):**
```
git init
git add -A
git commit -m "init: initial project setup"
```
"GitHub repo exists?" → if yes: `git remote add origin [url] && git push -u origin main` → confirm.

**CLEAN ON MAIN:**
"Git is clean. Ready."

**UNCOMMITTED CHANGES:**
"Complete or WIP?"
- Complete → commit now
- WIP → `git stash` → proceed

**OPEN BRANCH:**
"Complete or abandoned?"
- Complete → full close-out cycle (diff, verify, translate, review, commit, PR, log)
- Abandoned → `git branch -d [name]` → proceed

**NO REMOTE:**
"Create on GitHub: `git remote add origin [url] && git push -u origin main`"

---

## STEP 10 — Ready confirmation
Report: "System: [status]. Git: [status]. Last work: [summary]. Ready."

No task executes before step 10 is complete.
