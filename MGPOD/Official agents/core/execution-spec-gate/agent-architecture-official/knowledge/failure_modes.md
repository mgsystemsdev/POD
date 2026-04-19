# Failure modes (Spec Gate system)

| Failure | Cause | Prevention |
|---------|--------|------------|
| Invented requirements | Model fills gaps | BLOCK/ASK only; no task without REQ element |
| Wrong task order | Ignored infra or schema | `infrastructure_rules.md` + `depends_on` |
| Untestable execution | Vague `success_criteria` | Reject; map only Output + Done when |
| Silent wrong failure handling | Generic `failure_behavior` | Reject; map only Failure path |
| Orphan / multi-REQ tasks | Bad traceability | One `requirement_ref` per task |
| PRD dependency leak | Thin `description` | Full `description_template.md` |
| Cyclic or broken deps | Bad `depends_on` | DAG validation |
| Section B drift | User pasted partial B | `input_validation.md` ten-section gate |
| Duplicate work | 1:N not used when needed | Split REQ deliverables per `task_generation.md` |

## Operator symptoms (downstream)

- Execution stop-and-ask mid-task → `description` failed execution-independence test.
- Verification arguments → `success_criteria` not observable.
- Wrong rollback behavior → `failure_behavior` not from Failure path.
