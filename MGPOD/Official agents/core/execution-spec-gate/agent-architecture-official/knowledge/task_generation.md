# Task generation

## Role boundary

Spec Gate **translates** requirement contracts into tasks. It **does not** design features, choose libraries, or add requirements.

## Requirement → task mapping

| Case | Rule |
|------|------|
| **1:1** | Single REQ is one cohesive deliverable executable in one session (30–90 min) → **one task**. |
| **1:N** | REQ bundles multiple independently verifiable deliverables, distinct artifacts, or strict sequencing → **multiple tasks**, same `requirement_ref` on each. |
| **N:1** | **Forbidden.** One task MUST NOT satisfy multiple REQ-IDs. Split or BLOCK. |

## Atomic task sizing

- Target **30–90 minutes** of focused implementation per task.
- If a REQ cannot be decomposed without inventing scope → **BLOCK** (Architect must split REQ or clarify).

## Scope grouping

- Emit tasks in **execution order** within the JSON array.
- **Infrastructure** scope tasks (see `infrastructure_rules.md`) appear **before** feature scopes.
- Within a scope, keep **sub-scope** tasks contiguous when `tier` is 3.
- **Global `order`** implied by array index: first element runs first unless `depends_on` overrides start eligibility.

## Tier assignment (`tier` field)

| Tier | When |
|------|------|
| 1 | Small scope: typically 1–5 tasks for this REQ group |
| 2 | Standard: ~6–15 tasks |
| 3 | Large: 16+ tasks or explicit phased sub-scopes; use sub-scope in `title` pattern |

Derive from **Next Scope** + **Requirements** density; do not invent phases not implied by Section B.

## Title pattern

`[Scope] / [Sub-scope]: [Verb-led action]`

Sub-scope may be omitted for tier 1–2 when not used.

## Traceability

Every task **`requirement_ref`** = exactly one `REQ-###` from Section B. No orphan tasks; no tasks without REQ.
