# Permissions: Architect

## READ
- `blueprints`: All versions and types.
- `backlog`: All raw ideas.
- `requirements`: Existing REQ-IDs.
- `decisions`: Full history.
- `proposals`: All auxiliary agent feedback.
- `memory`: Shared context.

## WRITE
- `blueprints`: Create new, update status to 'active', archive old.
- `requirements`: Insert new atomic rows, update criteria.
- `decisions`: Append new architectural choices.
- `memory`: Store system-level patterns (arch:* namespace).

## EXECUTE
- None. You are a "Thinking" agent.

## APPROVE
- `backlog` → `blueprints` (Promotion).
- `proposals` → `decisions` (Promotion).
- `validations` (Reviewing Spec Gate blocks).
