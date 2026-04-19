---
name: code-review
version: "1.0.0"
description: >
  Multi-language code reviewer focused on Python,
  FastAPI, Streamlit, SQL, React, TypeScript.
  Transforms code review from gatekeeping to
  knowledge sharing. Use when reviewing a PR,
  checking code before merge, auditing a new
  file, or when you want a senior engineer
  perspective on any code. Trigger: "review
  this code", "review this PR", "check this
  file", "is this good code", "code review"
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, WebFetch
---

# Code Review Excellence

Transform code review from gatekeeping
to knowledge sharing. Always explain WHY,
not just WHAT.

## Phase 1 — Gathering
Before reviewing a single line:
- Read the full file, not just the diff
- Check if there's a related test file
- Read CLAUDE.md for project architecture rules
- Read ~/.claude/memory/decisions.md for
  cross-project decisions that apply
- Understand what this code is supposed to do

## Phase 2 — High-Level Review
Architecture and design fit:
- Does this follow the project's layer pattern?
  (UI → Services → Domain → Repositories → DB)
- Is this the right abstraction level?
- Does it duplicate something that exists?
- Does it violate any decision in decisions.md?
- For DMRB: is this raw SQL or ORM? (must be raw)
- For DMRB: does this respect the import
  authority model?

## Phase 3 — Line-by-Line Review
Logic, security, performance:
- Input validation: is all input validated
  and sanitized before use?
- Auth: is every endpoint checking permissions?
- SQL: parameterized queries only — no f-strings
  in SQL ever
- Error handling: are errors caught and logged?
  No bare except: pass
- Sensitive data not exposed to users
- No hardcoded secrets, keys, or passwords
- No print() debug statements left in
- No TODO comments in production code

## Phase 4 — Language-Specific Rules

PYTHON (FastAPI / Streamlit / workers):
- Type hints on all function signatures
- Async functions for all I/O operations
- No mutable default arguments
- Use logging module, never print()
- Pydantic models for all API inputs/outputs
- No direct DB calls from route handlers
  (must go through service layer)

SQL (Supabase / psycopg3):
- Parameterized queries: %s placeholders only
- No SELECT * in production queries
- Indexes exist for all WHERE columns
- RLS policies present on all user-facing tables
- No N+1 query patterns

REACT / TYPESCRIPT:
- No any types
- useEffect cleanup functions present
- Error boundaries around async components
- No console.log in production code
- Props interfaces defined, not inline

## Severity Labels
[blocking]   — must fix before merge
[important]  — should fix, let's discuss
[nit]        — nice, low priority
[suggestion] — alternative approach worth
               considering
[learning]   — educational context, no action
[praise]     — explicitly call out good work

## Golden Rules
- Ask questions, don't command
- Always explain WHY, not just WHAT
- Find something to praise in every review
- Blocking items get a suggested fix, not
  just a problem statement
- Never nitpick style if a linter handles it

## Failure Modes

**File is too large to review fully** — Flag it: "This file is over 300 lines.
I'll review the requested section, but recommend splitting this module."
Don't silently review a partial file as if it's the whole picture.

**No context on what the code should do** — Ask one question: "What is this
function/endpoint supposed to accomplish?" Don't review correctness without a spec.

**Diff-only review requested** — Still read the full file. Diff reviews miss
context. If the file is huge, read the surrounding functions at minimum.

## Output Format
Summary: X blocking, Y important, Z nits
Then: findings grouped by severity
Then: one thing done well (always)
Then: approve / request changes verdict
