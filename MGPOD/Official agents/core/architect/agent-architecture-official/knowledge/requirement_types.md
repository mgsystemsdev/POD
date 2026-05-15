# Requirement types

## Core types (mandatory — assign to every requirement)

| Type | Full name | Source | Authority |
|------|-----------|--------|-----------|
| **SR** | System Requirement | Blueprints, core architecture | Highest — overrides FR and FX |
| **FR** | Feature Requirement | Strategist output, validated proposals | Must respect SR |
| **FX** | Fix Requirement | Execution failures, Session Log corrections | Must reference original requirement |

## Type rules

**SR rules**
- Derived from Blueprints or system architecture — never from a proposal alone
- Cannot be overridden by FR or FX
- If a proposal conflicts with an SR → **BLOCK**; do not proceed until conflict resolved
- Changes to an SR require explicit architectural decision, recorded in Decisions tab

**FR rules**
- Adds new functionality to the system
- Must not violate any existing SR — if it does → **BLOCK** + state the conflict
- Cannot implicitly change data models, APIs, or agents defined by an SR
- Eligible for Backlog after APPROVED status

**FX rules**
- Corrects or adjusts existing behavior after an execution failure or validated defect
- **Must** carry `parent_requirement_id` referencing the original requirement — no exceptions
- Cannot introduce new architecture, new data models, or new agent responsibilities
- Attempting to add a feature inside an FX → **BLOCK**

## Subtypes (optional — add precision when useful)

| Subtype | Use for |
|---------|---------|
| DATA | Schema changes, DB migrations, data model adjustments |
| API | Endpoint definitions, request/response contracts |
| UI | Interface, layout, interaction behavior |
| INFRA | Deployment, environment, infrastructure config |
| AGENT | Agent behavior, agent communication rules |

Subtype never replaces core type. A requirement is always SR, FR, or FX first.

Examples: `FR + API`, `SR + DATA`, `FX + UI`

## Conflict resolution

Priority order (highest wins):

```
SR > FR > FX
```

- SR always wins over FR and FX
- If two SRs conflict → **BLOCK** until architectural decision made
- If FX scope creeps into FR territory → **BLOCK** + split into separate FX + FR

## Assignment rule

Architect **must** assign type before emitting any requirement. An untyped requirement is invalid and cannot reach VALIDATED state.
