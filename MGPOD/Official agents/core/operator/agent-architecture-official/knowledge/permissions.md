# Permissions: Operator

## READ
- `tasks`: Full queue and dependencies.
- `blueprints`: Canonical PRD and schema.
- `requirements`: To verify success criteria.
- `session_logs`: Prior session state.
- `memory`: Global patterns.

## WRITE
- `tasks`: Update status to `in_progress` or `done`.
- `session_logs`: Append new session records.
- `execution_trace`: Step-by-step tool usage logs.
- `decisions`: Choices made during building.
- `memory`: Operational patterns (op:*).

## EXECUTE
- Claude Code/Cursor workflows.
- Terminal commands (as guided by tools).

## APPROVE
- None. You execute; the human approves the final code.
