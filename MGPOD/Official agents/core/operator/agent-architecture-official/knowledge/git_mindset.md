# Git Mindset — The Operator

This is the mental model to enforce at every session. Miguel is building professional Git discipline through repetition.

---

## THE RULES

| Term | What it means | The rule |
|------|---------------|----------|
| `main` | Stable, always deployable | Never touch directly. Never commit to it. Never merge locally. |
| `branch` | One task, one unit of work | Create before execution. Delete after PR merge. |
| `commit` | One task, small and clear | One commit per task. No batching. Message: `[task-id]: [description]` |
| `push` | Work on GitHub | Push the branch before creating the PR. |
| `PR` | Reviewed before shipping | Always. No exceptions. Read it like someone else wrote it. |
| `merge` | After checklist passes | On GitHub UI only. Never locally. |
| `pull` | Sync before starting | After merge: `git checkout main && git pull origin main` |

---

## ENFORCEMENT

If Miguel violates any of these:
- Name the violation exactly
- Give the corrective command
- Explain in one plain English sentence why the rule exists

Never let a violation pass silently. Discipline builds through consistent correction.
