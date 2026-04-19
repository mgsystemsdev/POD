# The Configuration Format system

## System purpose

The Configuration Format system provides a tool-independent context layer that ensures Claude Code and Cursor operate from a single source of truth. Its primary purpose is to act as a **middle point** or thin adapter set that points these interfaces to a shared project knowledge bundle in `.claude/context/`, reducing re-explanation and eliminating context drift.

**Use cases:** repository onboarding through `agents init`, and maintaining architectural discipline during multi-tool execution sessions.

## Inputs

- **Global memory files** (`~/.claude/memory/`): authoritative source for operator identity (`user.md`), working standards (`preferences.md`), and durable global decisions (`decisions.md`).
- **Project knowledge bundle** (`.claude/context/`): project-specific source of truth including the PRD (`project.md`), work queue (`tasks.json`), and continuity log (`session.md`).
- **Codebase discovery** (`/init`): output from the built-in Claude Code `/init` command, which scans local file structures and build systems.

## Outputs

- **CLAUDE.md** (Claude Code adapter): project-root markdown with a **System** section (identity and PDOS rules) and a **Codebase** section (result of repository scan).
- **`.cursor/rules/00-context.mdc`** (Cursor adapter): structured rule file with a YAML header and pointers that ground the IDE in the shared `.claude/context/` bundle.
- **Validation reports**: console output confirming successful generation of tool pointers and alignment with the SQLite operational mirror.

## Key entities and schema

### The thin adapter

A configuration file that contains **instructions and pointers** rather than duplicated content stacks.

### CLAUDE.md schema

- **Identity / context**: pointers to global and project files (e.g. “Read `.claude/context/project.md`”).
- **Rules**: behavioral constraints (e.g. branch per task, PR before merge).
- **Divider**: horizontal line separating authored rules from generated codebase context.

### `.mdc` schema

- **Frontmatter**: metadata including `description` and `alwaysApply: true`.
- **Content**: context pointers and rules aligned with CLAUDE.md logic.

## Workflow

1. **Project initialization:** user runs `agents init`, which scaffolds `.claude/context/` and generates both thin pointer files (`CLAUDE.md` and `00-context.mdc`) simultaneously.
2. **Codebase scanning:** user runs `/init` inside Claude Code; the tool detects existing CLAUDE.md and appends findings below the divider.
3. **Synchronization:** during `agents push`, the sync worker regenerates the top **System** half of CLAUDE.md and `00-context.mdc` to reflect changes in global memory.
4. **Tool entry:** on session start, Claude Code reads CLAUDE.md and Cursor applies the `.mdc` rule so both tools see the same state without manual steps.

## Constraints

- **Duplication prohibition:** context must not be copied into tool adapters; adapters remain pointers to `.claude/context/` to avoid fragmentation.
- **Token budget:** CLAUDE.md length must stay pruned under **1500 tokens** to preserve the model’s reasoning window.
- **Write boundaries:** execution tools may write only within the working project directory and its subfolders.
- **Divider integrity:** the system section above the CLAUDE.md divider must never be overwritten by the codebase scan tool.

## Edge cases

- **Multiple tool installations:** detect and warn if both native and npm-based Claude Code are installed to avoid configuration conflicts.
- **Vague rules:** ambiguous CLAUDE.md instructions trigger **stop and ask**, not hidden assumptions.
- **Pathing conflicts:** if the project is moved, refresh adapters via `agents push` to update pointers to the knowledge bundle.
- **Exhausted budget:** if the primary tool’s token budget is hit, redirect to fallback adapters (Cursor or Gemini CLI).

## State handling

- **Authorship vs mirroring:** authoritative state lives in markdown on disk; SQLite is the operational mirror and control plane.
- **Baton preservation:** `analysis.md`, `plan.md`, and `handoff.md` pass context between tools and avoid redundant codebase scanning.
- **Session continuity:** every session ends by writing `session.md` and begins by reading it via adapter pointers.

## Failure handling

- **Loud diagnostics:** if pointer generation fails, block sync and report which file failed.
- **Fail-closed matching:** unmatched commands or invalid task IDs default to requiring manual human approval.
- **Reset protocol:** for structural drift, stop execution, document incorrect state, and return to design.

## Examples

### Scenario 1 — project onboarding

- **Input:** user runs `agents init` on an empty directory.
- **Expected output:** `.claude/context/` seeded with templates; `CLAUDE.md` created with the operator’s global standards; `.cursor/rules/00-context.mdc` generated with a header so it always applies in Cursor.

### Scenario 2 — codebase context integration

- **Input:** user runs `/init` in a repo that already contains a PDOS `CLAUDE.md`.
- **Expected output:** Claude Code scans the directory and appends technical stack details (e.g. FastAPI, SQLite, Python) **below the divider only**, leaving PDOS behavioral rules in the top section untouched.
