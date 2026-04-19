# The Sync Layer

## System purpose

The Sync Layer is the bridge between the **Knowledge Layer** (Layer 2) and the **control plane** (Layer 4 in the broader stack): it turns authored Markdown and JSON into database records so Claude Code, Cursor, and the dashboard share one operational picture. Sync is **one-way** (filesystem → SQLite) to prevent context drift.

---

## Inputs

| Input | Description |
| :--- | :--- |
| **Knowledge bundle** (`.claude/context/`) | `project.md`, `tasks.json`, `session.md`, `decisions.md`. |
| **Global memory** (`~/.claude/memory/`) | `user.md`, `preferences.md`, global decisions. |
| **Registry** (`projects_index.json`) | Slug → absolute project root. |
| **CLI flags** | e.g. `--slug`, `--dry-run`, `--no-tasks`. |

---

## Outputs

| Output | Description |
| :--- | :--- |
| **Operational state** | Updated `blueprints`, `tasks`, `decisions`, `session_logs`, `memory`. |
| **Tool adapters** | Regenerated `CLAUDE.md`, `.cursor/rules/00-context.mdc` (thin pointers). |
| **Validation report** | Console: what synced, registration/path errors. |

---

## Key entities and schema

### The baton

Files that pass context between tools without re-reading the whole repo:

- `analysis.md`, `plan.md`, `handoff.md`

### Sync-related concepts

| Concept | Notes |
| :--- | :--- |
| **Project registry** | `slug` (unique), `name`, `root_path` (absolute). |
| **Task schema** | `id`, `title`, `description`, `status`, `requirement_ref`, `done_condition`, `failure_behavior`. |
| **Tool configs** | Pointers only—no full content copies; reference `.claude/context/`. |

---

## Workflow

1. **Registry load** — `agentctl.sh` (or equivalent) reads `projects_index.json` for target paths.
2. **Artifact sync** — `push_claude_artifacts.py` reads `.claude/context/*.md`.
3. **Database mirroring** — Parsed content → `blueprints`, `decisions`, `session_logs`.
4. **Task ingestion** — `tasks.json` → atomic write to `tasks`.
5. **Config generation** — Regenerate `CLAUDE.md` / `.mdc` from global + project memory.
6. **Validation** — Final report: dashboard + tool alignment.

---

## Constraints

- **Unidirectional flow** — Disk → database only.
- **Atomic ingestion** — Any `tasks.json` error fails the whole import.
- **CLAUDE.md size** — Prune to stay under **1500 tokens**.
- **Isolated writes** — Claude Code writes only inside the project tree.

---

## Edge cases

| Case | Behavior |
| :--- | :--- |
| **Missing `.claude/context/`** | Skip project; “registration gap” in dashboard. |
| **Adapter generation failure** | Block sync so tools do not run on stale context. |
| **Duplicates** | Import dedupes by `(title, source='import')` per project where implemented. |
| **Stale registry path** | Sync fails loudly with diagnostics. |

---

## State handling

- **Authorship** — Repo files are truth; DB is the queryable mirror.
- **Trigger** — Manual `agents push` after session or task completion to “lock” state.

---

## Failure handling

- **Loud diagnostics** — Identify failing step (e.g. migration, malformed JSON).
- **Fail-closed** — Unknown commands / bad IDs → approval or skip + log.
- **Recovery** — Clear instructions to fix and retry.

---

## Examples

- `agents push --slug dmrb` after PRD edit → `blueprints` updated; `CLAUDE.md` refreshed; Blueprint tab matches disk.
- Invalid `task_id` in `tasks.json` → ingestion aborts; no partial `tasks` writes; error logged.
