# Defaults and constraints

## Default stack (when user silent)

State once; confirm if material to contracts.

| Layer | Default |
|-------|---------|
| Languages | Python primary; JS secondary when needed |
| HTTP API | FastAPI |
| Database | SQLite; **raw SQL** (`sqlite3`); parameterized; **no ORM** |
| Frontend | HTML/CSS simple dashboards; React only if in scope |
| VCS | Git; **branch per task**; PR to **main** |
| Shape | Monolith; **service layer** between HTTP and DB; **no** direct DB in route handlers |
| Host | Local-first |

**Not assumed unless PRD says:** ORM, Docker, managed cloud DB.

## Override rules

Overrides **only** if:

1. User states **explicitly**, and  
2. Section A updated (architecture / constraints / open assumptions), and  
3. Critical Constraints + Requirements stay consistent.

Conflicting override → **BLOCK** until resolved.

## Non-negotiables

- Five-element contracts + Done when for every in-scope REQ.
- Section B: **ten** sections, **fixed** order and headings ([system_contract.md](system_contract.md)).
- No silent assumptions ([validation.md](validation.md)).
- Artifacts under `.claude/context/`.
- **Infrastructure-first** task ordering: data model + migration/setup explicit in Section A before dependent feature REQs ([translation_rules.md](translation_rules.md)).
- **Traceability:** one `requirement_ref` per task ([task_spec.md](task_spec.md)).

## Workflow invariants (system)

- Files = authored truth; DB/dashboard = mirrors after ingest.
- **WIP = 1** task in progress.
- **Analyze → plan → execute**; minimal changes; only planned files per step.
- Automation only after manual proof.

## Security baseline

- Secrets not in repo; env for keys.
- AuthZ explicit if multi-user or sensitive data.
- If user skips security → **ASK** once for threat boundary; else record in Section A open risks as “unverified.”
