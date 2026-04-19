# Requirement contract (Operator knowledge)

Use this checklist when validating a task or change before marking work done.

- **TRIGGER:** What event starts this behavior?
- **INPUT:** What inputs are accepted and validated?
- **OUTPUT:** What exact shape or behavior must the output have?
- **CONSTRAINTS:** What must never happen (limits, auth, data rules)?
- **FAILURE PATH:** What happens when validation fails or dependencies error?

Each implementation should state how it satisfies these five dimensions.
