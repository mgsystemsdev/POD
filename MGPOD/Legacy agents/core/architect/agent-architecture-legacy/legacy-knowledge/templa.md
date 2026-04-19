# TEMPLATES — ARCHITECT OUTPUT SYSTEM (FINAL)

---

## PURPOSE

This document defines the **exact structure of all outputs** produced by The Architect.

No deviation allowed.
If output does not match → it must be regenerated.

---

## 0. ANCHOR SEQUENCE (STRICT ORDER — ENFORCED)

The Architect must build the system in this exact order:

1. Core Problem
2. Core User Action
3. Requirements (REQ contracts)
4. Data Model
5. Workflow
6. Architecture
7. Technical Specs
8. Integrations
9. Constraints & Guardrails
10. Failure Handling
11. State Management
12. MVP Scope
13. Open Assumptions

---

### ENFORCEMENT RULES

* Do not skip any step
* Do not reorder
* Do not jump ahead prematurely
* Do not generate output until all steps are complete

---

### FAILURE CONDITION

If any step is incomplete or out of order:

→ BLOCK output
→ Return to missing step
→ Continue questioning

---

### PURPOSE OF SEQUENCE

Ensures:

* Correct dependency flow
* No premature decisions
* Complete system coherence

---

## 1. PRIMARY OUTPUT

The Architect produces ONE document:

project.md

* Section A → Full PRD
* Section B → Handoff Summary

Both must be produced together.

---

## 2. SECTION A — FULL PRD STRUCTURE

### 1. System Identity

* Name
* Type
* Problem
* Users
* Success condition

---

### 2. Requirements (MANDATORY)

Each requirement must include:

REQ-ID: [Name]

Trigger:
Input:
Output:
Constraints:
Failure Path:

Done when:

---

### 3. Data Model

* Entities
* Fields (type, required, constraints)
* Relationships
* Status values
* Allowed transitions

---

### 4. Core Workflow

* Entry point
* Step-by-step flow
* Decision branches
* Exit condition
* Edge cases

---

### 5. Architecture

* System type
* Layers
* Components
* Communication
* External dependencies
* Constraints
* Forbidden patterns

---

### 6. Technical Specifications

* Business rules
* Validation rules
* Performance targets
* Error format
* Logging

---

### 7. File Structure

Project directory layout

---

### 8. API Contracts (if applicable)

* Endpoints
* Inputs
* Outputs

---

### 9. Success & Failure Conditions

* Success criteria
* Failure conditions
* Known risks

---

### 10. Open Assumptions

* Unverified conditions

---

### 11. MVP Scope

* In scope
* Deferred
* Out of scope

---

## 3. SECTION B — HANDOFF SUMMARY

Must include:

* Project name
* System type
* Architecture summary
* Critical constraints
* MVP scope
* Out of scope
* Requirements (1-line per REQ)
* File structure (compact)
* Current state
* Next scope

---

## 4. STRUCTURE ENFORCEMENT

* All sections must exist
* No missing requirement elements
* No undefined entities
* No structural inconsistencies
* No extra sections

---

## 5. SCHEMA ALIGNMENT

If structured output required:

* Must align with schema.json
* All required fields present
* No extra fields
* Correct data types

---

## 6. FAILURE CONDITIONS

If any of the following occur:

* Missing section
* Missing requirement field
* Incorrect format
* Sequence violation
* Structural inconsistency

→ Output is INVALID
→ Must regenerate

---

## 7. OBJECTIVE

Ensure every output is:

* Structured
* Complete
* Validated
* Execution-ready

Templates enforce final system integrity.
