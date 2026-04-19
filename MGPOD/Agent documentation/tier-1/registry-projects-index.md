# The Registry (projects_index.json)

## System purpose

The Registry (`projects_index.json`) is the central inventory and project-routing authority of the Personal Developer OS. It maps project slugs to absolute filesystem paths so sync workers, dashboard services, and AI agents can locate project-specific context (`.claude/context/`) without manual navigation. It bridges the **knowledge layer** (files) and the **control plane** (database).

## Inputs

- **Initialization signal:** triggered by `agents init [path]`, which scaffolds the project and starts registration.
- **Manual registration:** commands such as `agents add [slug] [name]` or `agents register <slug> <name> <root_path>`.
- **Auto-discovery (v1.3+):** `init.sh` captures `root_path` and slug for any project that runs it.
- **Environment context:** resolves `Path.home()` for database and project path consistency.

## Outputs

- **Canonical inventory:** structured JSON (consolidated under `agent-os/config/` rather than duplicated across services).
- **Dashboard sync:** FastAPI uses it to populate the project sidebar and filter tasks, blueprints, and logs by `project_id` or slug.
- **Worker routing:** supplies root directory for `push_claude_artifacts.py` and `task_worker.py` to find `.claude/tasks.json` and `.claude/context/project.md`.

## Key entities and schema

### Project object schema

| Field | Type | Validation rule |
| :--- | :--- | :--- |
| `project_id` | String | Unique slug (e.g. `dmrb`, `quick-agent-job`). |
| `project_name` | String | Human-readable dashboard name. |
| `project_path` | String | Absolute path to repository root. |
| `type` | Enum | `system` (OS core) or `app` (managed project). |
| `status` | String | `active` or `archived`. |
| `registered_on` | Date | ISO 8601 (`YYYY-MM-DD`). |

## Workflow

1. **Onboarding:** user runs `agents init` in a new project directory.
2. **Path resolution:** script determines absolute path and prompts for a unique project slug.
3. **JSON update:** entry appended to `projects_index.json`.
4. **Database sync:** registry triggers `POST /api/projects` to create a matching SQLite `projects` row.
5. **Artifact injection:** worker uses registry path to locate and sync `.claude/context/` into the operational mirror.

## Constraints

- **No path fragility:** entries must point to existing directories; missing paths surface a **registration gap**.
- **Uniqueness:** duplicate slugs or names are forbidden to avoid dashboard routing collisions.
- **V3 portability:** absolute paths must support environment-aware resolution (e.g. `/Users/...` vs `/home/...` on VPS).
- **Dashboard requirement:** manual `agents add` / `register` need the dashboard on port **8765** to keep JSON and SQLite in sync.

## Edge cases

- **Registration drift:** project renamed or moved without updating the registry → workers skip the project; dashboard flags **missing path**.
- **Duplicate globals:** tasks with no project slug in `~/.claude/tasks.json` route to `claude-global` until re-slugged (e.g. via `migrate_claude_global_tasks.py`).
- **Subfolder collision:** nested projects (e.g. `dmrb-legacy` under `DMRB_PROD`) → registry treats as one project unless registered as separate entities.

## State handling

- **Primary persistence:** `projects_index.json` is source of truth for repository locations.
- **Operational mirror:** SQLite `projects` table is runtime state for dashboard and API.
- **Atomic sync:** bulk path updates must update JSON and SQLite together to avoid disconnection.

## Failure handling

- **Loud diagnostics:** if `agents push` finds a registered project without root path or `.claude/context/`, exit with a clear diagnostic.
- **Sync recovery:** if JSON and DB drift, `agents push` with an updated registry reconciles operational state.

## Examples

### `agents add`

- **Input:** `agents add dmrb "DMRB Production"` from `~/Projects/active/DMRB_PROD`.
- **Expected output:** entry in `projects_index.json` with absolute path; new SQLite row; sidebar shows **DMRB Production**.

### Sync worker

- **Input:** worker reads registry for project `quick-agent-job`.
- **Expected output:** resolves path (e.g. `/Users/.../quick-agent-job`), finds `.claude/context/`, imports tasks into the database.
