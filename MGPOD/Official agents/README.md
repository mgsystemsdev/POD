# Official agents

**Canonical** prompts and knowledge for PDOS. Load these into ChatGPT, Cursor rules, or any tool that should follow current behavior.

## Layout

| Path | Contents |
|------|----------|
| `Official agents/core/<role>/` | Pipeline agents: Architect, Execution Spec Gate, Operator, Strategist (auxiliary), Blueprint Creator, etc. |
| `Official agents/core/<role>/agent-architecture-official/` | `prompt/` + `knowledge/` — active system prompt and knowledge tree |
| `Official agents/auxiliary/<role>/` | Specialist advisors (senior_dev, database_specialist, …) — same `agent-architecture-official/` layout |

Role-level files (e.g. `architect/README.md`, `architect/vertical-data-flow.md`) live next to `agent-architecture-official/` under that role.

## Legacy material

Archived prompts and knowledge live under **`Legacy agents/`** (mirror structure: `core/` and `auxiliary/`). Do not load legacy trees as canonical.
