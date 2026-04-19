---
name: review
version: "1.0.0"
description: >
  Run all 3 hardening agents (devil-advocate, security-reviewer, drift-detector) against
  any output, decision, or code change. Produces a single SHIP / REVISE / BLOCK verdict.
  If BLOCK: generates fix tasks and appends to ~/.claude/tasks.json.
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Trigger phrases

"review this", "check this", "devil's advocate", "security check", "is this safe to ship",
"run a review", "harden this", "challenge this", "scan for vulnerabilities", "check for drift"

# Mission

Gate every output through three independent hardening agents before anything ships.
No output is approved by a single voice. All three agents must run.

# Execution flow

Run agents 1–3 in parallel, then aggregate:

## Agent 1 — devil-advocate
- Read the proposed solution or decision in full
- Identify the **3 strongest counter-arguments**
- Identify the **most likely failure mode**
- Identify **what was NOT considered**
- Score confidence: HIGH / MEDIUM / LOW
  - LOW → BLOCK: revision required before proceeding
  - MEDIUM → WARN: list conditions that must be met
  - HIGH → APPROVE with notes (never silent)

## Agent 2 — security-reviewer
- Grep for hardcoded secrets or credentials (`password=`, `secret=`, `api_key=`, `token=`)
- Check for SQL / command injection vectors
- Check for unvalidated inputs at system boundaries
- Check for missing auth checks on any endpoint or action
- Check for dangerous file operations (`rm -rf`, `unlink`, `os.remove` without guards)
- Check for exposed API endpoints without rate limiting
- Output: PASS / WARN / BLOCK with specific `file:line` findings
- **BLOCK means nothing ships until fixed**

## Agent 3 — drift-detector
- Read `~/.claude/memory/decisions.md` first
- Read original task spec from inputs
- Compare final output against spec:
  - Flag scope additions **not in original spec**
  - Flag requirements from spec **not addressed**
  - Flag architectural decisions contradicting `decisions.md`
- Output: ALIGNED / DRIFTED with specific deltas

## Aggregation — final verdict

| devil-advocate | security-reviewer | drift-detector | Final verdict |
|---------------|------------------|----------------|---------------|
| APPROVE       | PASS             | ALIGNED        | **SHIP**      |
| WARN (any)    | WARN (any)       | DRIFTED (any)  | **REVISE**    |
| BLOCK (any)   | BLOCK (any)      | —              | **BLOCK**     |

BLOCK from **any single agent** overrides all others → final verdict is BLOCK.

## If BLOCK

1. Generate fix tasks for each blocking finding
2. Append tasks to `~/.claude/tasks.json` with:
   - `action_type: "claude_execute"`
   - `priority: 1`
   - `status: "pending"`
   - Task ID format: `rev-YYYYMMDD-NNN`
3. Report: "Swarm output BLOCKED. N fix tasks created. Nothing ships until tasks complete."

# Output format

```
## Review Report — [timestamp]

### devil-advocate
Confidence: HIGH | MEDIUM | LOW
Counter-arguments: [list]
Failure mode: [description]
Unconsidered: [list]
Verdict: APPROVE | WARN | BLOCK

### security-reviewer
Checks performed: [list]
Findings: [file:line — severity — description] or NONE
Verdict: PASS | WARN | BLOCK

### drift-detector
Spec requirements: [list]
Addressed: [list]
Missing: [list]
Scope additions: [list]
Verdict: ALIGNED | DRIFTED

---
FINAL VERDICT: SHIP | REVISE | BLOCK
[If BLOCK: list fix tasks created]
```
