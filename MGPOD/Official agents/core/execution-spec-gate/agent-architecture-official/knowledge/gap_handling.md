# Gap handling

## Critical gap (BLOCK)

**BLOCK** = emit a single JSON object (not an array): `{"_gate":"BLOCK","reasons":["string", "..."],"return_to":"Architect"}` — no task objects.

A gap is **critical** if any of:

- Missing Section B section or REQ contract element
- **Untestable** Output / Done when / success path
- **Missing or vague** Failure path (cannot derive `failure_behavior`)
- Persistence or integration change **without** enough detail to order tasks or write `description` without guessing
- **Contradiction** between Architecture, Critical Constraints, and Requirements

Response: name **exactly** what is missing or contradictory; state **Architect** must fix; **no tasks**.

## Non-critical ambiguity (ASK)

**ASK** = at most **one** focused question **or** **three-option protocol** (not both in same turn for the same gap).

Use **ASK** when:

- Architecture fork (two valid stacks/patterns) blocks faithful translation
- Ordering between two tasks is ambiguous but contract is otherwise complete

## Three-option protocol

When ASK is used for a fork, output **exactly three** labeled options **A / B / C** with tradeoffs; **no** fourth “hybrid” unless user must pick from stated combinations. User selection becomes the only allowed interpretation; **do not** proceed until selection is in the new input.

## Never

- Guess missing contracts
- Silently pick defaults
- Generate “placeholder” tasks for unclear scope
