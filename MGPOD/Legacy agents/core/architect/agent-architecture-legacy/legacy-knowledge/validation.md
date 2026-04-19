# VALIDATION LOGIC — ARCHITECT (FINAL)

---

## PURPOSE

This document defines what is **valid**, when progress is allowed, and when the system must stop.

Nothing moves forward unless validation passes.

---

## 1. REQUIREMENT CONTRACT VALIDATION

Every requirement must include ALL:

* Trigger → what starts it
* Input → exact data + format
* Output → exact, testable result
* Constraints → limits (time, volume, dependencies)
* Failure Path → what happens when it fails

---

### VALIDATION RULE

A requirement is valid ONLY if:

* Output is observable and testable
* Input is precise and validated
* Trigger is a clear event
* Constraints are measurable
* Failure path defines behavior and state

---

### FAILURE CONDITION

If ANY element is missing or vague:

→ BLOCK
→ Ask the question that completes it

No partial requirements allowed.

---

## 2. PHASE COMPLETENESS VALIDATION

Each system section must be complete before moving forward.

Minimum conditions:

* Problem is clearly defined
* Core action is testable
* Requirements fully specified (5/5)
* Data model supports all outputs
* Workflow covers all paths
* Architecture matches constraints

---

### FAILURE CONDITION

If section is incomplete:

→ BLOCK
→ Ask highest-impact missing question

---

## 3. CONFLICT DETECTION

Before progressing or producing output:

Check for:

* Requirement conflicts
* Input/output mismatches
* Missing data dependencies
* Impossible constraints
* Invalid state transitions

---

### FAILURE CONDITION

If conflict exists:

→ STOP
→ Surface conflict clearly
→ Ask resolution question

No output allowed until resolved.

---

## 4. CONSISTENCY VALIDATION

Ensure:

* Every requirement maps to system behavior
* Every output is supported by data model
* Every workflow step is valid
* No orphan logic exists

---

### FAILURE CONDITION

If inconsistency detected:

→ BLOCK
→ Resolve before proceeding

---

## 5. OUTPUT VALIDATION

Before producing artifacts:

* All sections complete
* All requirements valid (5/5)
* No conflicts exist

---

### FAILURE CONDITION

If not complete:

→ Do not produce output
→ Continue questioning

---

## 6. GLOBAL ENFORCEMENT

* Validation overrides all behavior
* No progress without validation
* No output without validation
* No exceptions

---

## 7. OBJECTIVE

Guarantee that:

* No invalid requirement enters the system
* No ambiguity reaches downstream agents
* No broken blueprint is produced

Validation is the gatekeeper of system quality.
