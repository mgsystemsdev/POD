# Description template (mandatory)

Every task `description` MUST be plain text containing **all six** labeled blocks **in this order**:

```
OBJECTIVE:
[One to three sentences: what this task delivers]

REQUIREMENT:
[requirement_ref]: [Plain English restatement of full contract — Trigger, Input, Output, Constraints, Failure path]

ARCHITECTURAL CONSTRAINTS:
- [Bullet: Critical Constraints + Architecture snippets that bind this task]
- [Add bullets until all applicable constraints are listed]

DONE WHEN:
[Single testable condition aligned with Done when + Output]

FAILURE BEHAVIOR:
[Restate Failure path as implementation obligations]

DO NOT:
- [Forbidden actions from Critical Constraints / Architecture / REQ Constraints]
- [Continue until explicit forbiddens from contract are listed]
```

## Rules

- **OBJECTIVE** ≠ vague; names the concrete artifact or behavior change.
- **REQUIREMENT** must not omit Input invalid cases or Failure path effects.
- **ARCHITECTURAL CONSTRAINTS** / **DO NOT**: if none apply, line: `N/A — [reason]` under that block (only if truly none).
- No Markdown outside these blocks except bullets inside the list sections.
