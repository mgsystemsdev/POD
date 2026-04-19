# Version Control (Layer 7)

## System purpose

Version Control (Layer 7) is the permanent, authoritative record of what has shipped in the Personal Developer OS. It enforces **team-style workflows for a solo developer**: isolated changes, self-review via Pull Requests, and a stable, deployable `main` branch.

## Inputs

- **Active task ID** (e.g. `TASK-001`): used to name isolated branches.
- **PRD and knowledge bundle:** `.claude/context/` files committed to Git so architectural versions are not lost.
- **Verified code changes:** staged changes from Claude Code or Cursor after Layer 4 verification.
- **Clean main state:** local environment updated and synced with GitHub before new work.

## Outputs

- **Isolated task branches:** short-lived branches per unit of work (e.g. `feature/TASK-001`).
- **Atomic commits:** 1:1 mapping between a completed dashboard task and a Git commit.
- **GitHub Pull Requests:** mandatory review artifact via GitHub UI for every task.
- **Stable main branch:** protected line reflecting only approved, merged PRs.

## Key entities and schema

- **Branch naming:** `<type>/<task-id>` (e.g. `feature/TASK-042`, `fix/TASK-101`).
- **Commit message:** `[task-id]: [brief description]`.
- **Git gate:** mandatory check at session start and task start — clean `main`, pulled latest.
- **Self-review checklist:** five questions the Operator uses during PR to simulate peer review.

## Workflow — execution loop

The Operator GPT enforces this sequence:

1. **Session start — Git gate:** on `main`, pull latest, working tree clean.
2. **Task selection:** highest-priority pending task from the dashboard.
3. **Branch creation:** isolated branch named for task ID; execution blocked until branch exists.
4. **Execute and verify:** work on branch; pass REQ-008 verification gate.
5. **Diff check:** `git diff` confirms only plan-authorized files changed.
6. **Review ready:** plain-English summary of changes.
7. **Atomic commit:** exactly one commit for the task after verification.
8. **PR gate:** push branch; open PR in **GitHub UI** (never merge locally only).
9. **Self-review:** walk checklist inside the PR.
10. **Merge and pull:** merge on GitHub; delete remote/local branch; return to `main`; pull.
11. **Close task:** mark task done in dashboard to stay aligned with Git history.

## Constraints

- **No main writes:** no code commits directly on `main`.
- **WIP = 1:** one task/branch in progress at a time.
- **GitHub UI rule:** merges through GitHub PR interface to build review habit.
- **1:1 rule:** every commit traces to exactly one PRD requirement.

## Failure handling — drift control

| Drift | Response |
| :--- | :--- |
| Working on `main` | Hard stop; `git checkout -b <branch>` before continuing. |
| Batching commits | Block PR; reset or split commits. |
| Local merge attempt | Reject; use GitHub UI. |
| Skipping PR | Block dashboard task completion if no PR merge detected. |

## State handling

- **Authorship:** Git history holds permanent project truth (PRDs, tasks, decisions).
- **Continuity:** session logs and decisions committed end-of-task for next session context.
- **Operational mirror:** SQLite reflects current state but does not overwrite Git; flow is Git-tracked files → DB via `agents push`.

## Examples

### Task initialization

- **Input:** select `TASK-012` — add login validation.
- **Expected:** `git checkout main && git pull origin main`, then `git checkout -b feature/TASK-012`.

### Task completion

- **Input:** verified changes for `TASK-012`.
- **Expected:** `git add -A && git commit -m "TASK-012: implement login validation"`, then `git push origin feature/TASK-012` and open PR in GitHub UI.
