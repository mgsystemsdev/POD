# Translation rules (mechanical)

## Field mapping

| REQ contract element | Task field |
|---------------------|------------|
| **Output** + **Done when** | `success_criteria` (single string; observable) |
| **Failure path** | `failure_behavior` |
| **Trigger** + **Input** + **Constraints** (+ applicable **Architecture** / **Critical Constraints** snippets) | `description` (within template blocks) |
| REQ identity | `requirement_ref` |
| Ordering vs other tasks | `depends_on` |

## description

`description` **is** the execution prompt. **No paraphrase that drops validation rules.** Copy contract facts; restate in imperative execution language; do not add facts not in Section B.

## success_criteria

- Must be **falsifiable** (specific signals: tests, HTTP codes + body shape, CLI exit, migration applied, UI state).
- Must align with **Done when**; must not contradict **Output**.

## failure_behavior

- Must specify what the system does on failure per contract (retries, state stored, user-visible result, side effects).
- If Failure path absent in REQ → **BLOCK** (do not invent).

## Constraints in description

Under **ARCHITECTURAL CONSTRAINTS** and **DO NOT**, include every Section B **Critical Constraints** and REQ **Constraints** that apply to this task. Omit none that apply; do not add constraints not stated.

## Forbidden

- Inventing DDL, endpoints, files, or behaviors not implied by Section B.
- Filling gaps with “typical” or “standard” patterns without explicit text in input.
