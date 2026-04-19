# Persistence contract

## Canonical store

https://pod-production-63e3.up.railway.app — all reads and writes go here via ChatGPT Actions (X-API-Key auth).

## Field mapping

| Artifact | API call | Key fields |
|----------|----------|-----------|
| `project.md` (Section A + B) | POST `/api/projects/{id}/blueprints` or PUT `/api/blueprints/{id}` | `type: "prd"`, `title = project name`, `content = full Section A+B markdown`, `version` |
| `schema.json` | POST `/api/projects/{id}/blueprints` or PUT `/api/blueprints/{id}` | `type: "schema"`, `title = project name`, `content = JSON.stringify(schema)`, `version` |
| Architecture decision | POST `/api/projects/{id}/decisions` | `title`, `content` |
| Project-scope KV | PUT `/api/projects/{id}/memory/{key}` | `value` (string) |

## Call order per mode

| Mode | Session start | After emit |
|------|---------------|-----------|
| MODE 0 (bundle import) | GET projects → match by name → GET blueprints (type=prd, type=schema) → read existing versions | POST or PUT blueprints (prd + schema) |
| MODE 1 (raw idea) | GET projects → confirm project exists or ask user for project_id | POST blueprints (prd + schema) after emit |
| MODE 2 (PRD update) | GET projects → GET blueprints → GET blueprint by id → read current version | PUT blueprints (increment version) |
| MODE 3 (proposal review) | GET projects → GET blueprints → GET decisions | POST or PUT blueprints if changes result |

**Rule:** Always GET before PUT. Never assume blueprint_id — resolve it from the list.

## Version discipline

1. GET existing blueprint to read current `version` field.
2. Increment: `new_version = current_version + 1`.
3. PUT with `version: new_version`.
4. Never PUT the same version number twice (version conflict = data loss risk).

## Error handling

| HTTP status | Architect response |
|-------------|-------------------|
| 4xx (client error) | BLOCK emit. State the error. Fix input before retrying. Do not emit artifacts. |
| 5xx (server error) | Retry once. If still 5xx → emit artifacts as text in chat with user-visible warning: "Dashboard write failed — save manually." |
| 401 Unauthorized | BLOCK. Inform user: "API key missing or invalid. Check ChatGPT Actions → Authentication → X-API-Key." |
| 404 project not found | BLOCK. Ask user: "No project found for that name. List projects and confirm which id to use." |
| Version conflict | BLOCK. GET blueprint again, read latest version, re-attempt PUT with correct version. |
