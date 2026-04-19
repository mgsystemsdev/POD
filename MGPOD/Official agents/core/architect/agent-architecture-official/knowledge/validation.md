# Validation

**Validation overrides progress.** Invalid state → **no** Section A + B + schema emit.

## Contract validation (per REQ)

Valid only if:

| Check | Rule |
|-------|------|
| Five elements | Trigger, Input, Output, Constraints, Failure path present and **non-vague** |
| Output | Observable / testable ([requirement_contract.md](requirement_contract.md) test) |
| Input | Valid **and** invalid cases |
| Failure path | Concrete: state, retries, visibility — not “handle errors” |
| Done when | Present; maps to Output |

Failure → **BLOCK** that REQ; **ASK** one question (highest-impact gap).

## Conflict detection (BLOCK until resolved)

| Type | Examples |
|------|-----------|
| Requirement | Two REQs mutate same state; Output of one breaks Input of another; Constraint makes REQ impossible |
| Data model | Field required by Output missing; illegal state transition |
| Architecture | REQ implies pattern forbidden by Critical Constraints |

**Action:** State conflict in one sentence; require precedence or change. **No** emit until resolved.

## Consistency

- Every REQ traceable to workflow or user journey.
- No orphan outputs (Output without entity/API/UI support in model or architecture).

## No silent assumptions

- Unknown fact → **ASK** / **GUIDE**, or assumption **verbatim** + explicit user **Y/N** before PRD.
- **Never** add facts because they “usually” apply.

## Blocking conditions (output gate)

**Do not** emit `project.md` + `schema.json` if:

- Any in-scope REQ fails contract validation
- Any conflict unresolved
- Section B missing any of **ten** sections or wrong order/headings ([system_contract.md](system_contract.md))
- `schema.json` out of sync with Section A data model (when model exists)
- Pre-output simulations fail: Spec Gate (tasks generable?), Execution (description sufficient?), Verification (objective proof?)

## Loud failure

Invalid session → **failed session**. Do not direct user to Spec Gate.
